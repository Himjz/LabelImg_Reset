import os
import shutil
import re
import logging
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutoPyQtMigrator:
    def __init__(self, target_dir, exclude_dirs=None, exclude_files=None):
        """
        初始化自动迁移工具
        :param target_dir: 目标目录路径
        :param exclude_dirs: 要排除的目录列表
        :param exclude_files: 要排除的文件列表
        """
        self.target_dir = Path(target_dir).resolve()
        if not self.target_dir.exists():
            raise ValueError(f"目标目录不存在: {self.target_dir}")

        # 备份目录命名格式
        self.backup_pattern = "backup_"
        self.backup_dir = None

        # 获取当前脚本的文件名（用于排除备份）
        self.script_name = os.path.basename(__file__)

        # 默认排除的目录
        self.exclude_dirs = set(exclude_dirs or [])
        self.exclude_dirs.update([
            'venv', 'env', '.env',  # 排除虚拟环境
            '__pycache__', '.git',  # 排除缓存和版本控制
            'build', 'dist', '*.egg-info'  # 排除打包目录
        ])

        # 默认排除的文件
        self.exclude_files = set(exclude_files or [])
        self.exclude_files.update([
            self.script_name,  # 排除迁移脚本本身
            'migration.log'  # 排除日志文件
        ])

        # 核心替换规则
        self.replace_rules = [
            # 模块导入替换
            (r'from\s+PyQt5(\.\w+)?\s+import', r'from PySide6\1 import'),
            (r'import\s+PyQt5(\.\w+)?', r'import PySide6\1'),

            # 信号与槽装饰器和类
            (r'@pyqtSlot', r'@Slot'),
            (r'@pyqtProperty', r'@Property'),
            (r'pyqtSignal', r'Signal'),
            (r'pyqtSlot', r'Slot'),
            (r'pyqtProperty', r'Property'),

            # 类型替换
            (r'QString\((.*?)\)', r'str(\1)'),
            (r'QVariant\((.*?)\)', r'\1'),
            (r'QList<(.*?)>', r'list[\1]'),
            (r'QDict<(.*?),\s*(.*?)>', r'dict[\1, \2]'),
            (r'QSet<(.*?)>', r'set[\1]'),
            (r'QByteArray\((.*?)\)', r'bytes(\1)'),

            # 正则表达式相关
            (r'QRegExp', r'QRegularExpression'),
            (r'QRegExpValidator', r'QRegularExpressionValidator'),

            # UI加载
            (r'uic\.loadUi\((.*?)\)', r'QUiLoader().load(\1)'),
            (r'PyQt5\.uic\.loadUi\((.*?)\)', r'QUiLoader().load(\1)'),

            # 应用程序初始化
            (r'QApplication\(sys\.argv\)',
             r'QApplication(sys.argv)\n    QApplication.setStyle("Fusion")'),

            # 日志和调试
            (r'qDebug\((.*?)\)', r'print(f"Debug: \1")'),
            (r'qWarning\((.*?)\)', r'print(f"Warning: \1")'),
            (r'qCritical\((.*?)\)', r'print(f"Critical: \1")'),

            # 文件系统操作
            (r'QFile\.exists\((.*?)\)', r'os.path.exists(\1)'),
            (r'QFile\.remove\((.*?)\)', r'os.remove(\1)'),
            (r'QDir\.currentPath\(\)', r'os.getcwd()'),
            (r'QDir\.homePath\(\)', r'os.path.expanduser("~")'),

            # 翻译相关
            (r'QApplication\.translate\((.*?)\)', r'QCoreApplication.translate(\1)'),

            # 布局和边距
            (r'setMargin\((\d+)\)', r'setContentsMargins(\1, \1, \1, \1)'),

            # 图形绘制
            (r'QPixmap\.scaledToWidth\((\d+)\)',
             r'QPixmap.scaledToWidth(\1, QtCore.Qt.SmoothTransformation)'),
            (r'QPixmap\.scaledToHeight\((\d+)\)',
             r'QPixmap.scaledToHeight(\1, QtCore.Qt.SmoothTransformation)'),

            # 线程操作
            (r'QThread\.Sleep\((.*?)\)', r'QThread.sleep(\1)'),
            (r'QThread\.msleep\((.*?)\)', r'QThread.msleep(\1)'),
            (r'QThread\.usleep\((.*?)\)', r'QThread.usleep(\1)'),
        ]

        # 记录处理过的文件
        self.processed_files = []
        self.failed_files = []

    def find_latest_backup(self):
        """查找最新的备份目录"""
        backup_dirs = []
        for item in self.target_dir.iterdir():
            if item.is_dir() and item.name.startswith(self.backup_pattern):
                backup_dirs.append(item)

        if not backup_dirs:
            return None

        # 按名称排序（包含时间戳），取最新的
        return sorted(backup_dirs, key=lambda x: x.name, reverse=True)[0]

    def should_exclude(self, path):
        """检查路径是否应该被排除"""
        path = Path(path)
        file_name = path.name

        # 排除指定文件
        if file_name in self.exclude_files:
            return True

        # 排除指定目录
        for exclude in self.exclude_dirs:
            if exclude in str(path) or path.name == exclude:
                return True

        # 排除备份目录
        if self.backup_dir and str(self.backup_dir) in str(path):
            return True

        return False

    def backup_file(self, file_path):
        """备份文件并保持目录结构"""
        try:
            rel_path = file_path.relative_to(self.target_dir)
            backup_path = self.backup_dir / rel_path

            # 创建备份目录
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # 复制文件（保留元数据）
            shutil.copy2(file_path, backup_path)
            logger.debug(f"已备份文件: {file_path} -> {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"备份文件失败 {file_path}: {str(e)}")
            return None

    def add_missing_imports(self, content):
        """添加必要的导入语句"""
        imports_to_add = []

        # 如果使用了QUiLoader但没有导入
        if 'QUiLoader' in content and 'from PySide6.QtUiTools import QUiLoader' not in content:
            imports_to_add.append('from PySide6.QtUiTools import QUiLoader')

        # 如果使用了os.path但没有导入os
        if re.search(r'os\.path\.\w+', content) and 'import os' not in content:
            imports_to_add.append('import os')

        # 添加缺失的导入
        if imports_to_add:
            # 在现有导入之后添加
            if re.search(r'^import', content, re.MULTILINE):
                # 找到最后一个导入行
                lines = content.split('\n')
                last_import = -1
                for i, line in enumerate(lines):
                    if line.startswith(('import', 'from')):
                        last_import = i

                if last_import != -1:
                    lines = lines[:last_import + 1] + imports_to_add + lines[last_import + 1:]
                    return '\n'.join(lines)

            # 如果没有导入，在文件开头添加
            return '\n'.join(imports_to_add) + '\n' + content

        return content

    def process_file(self, file_path):
        """处理单个Python文件"""
        file_path = Path(file_path)

        # 检查是否为Python文件且不应被排除
        if not file_path.suffix == '.py' or self.should_exclude(file_path):
            return False

        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # 应用所有替换规则
            for pattern, replacement in self.replace_rules:
                content = re.sub(
                    pattern,
                    replacement,
                    content,
                    flags=re.MULTILINE
                )

            # 添加必要的导入
            content = self.add_missing_imports(content)

            # 只有内容改变时才写入文件
            if content != original_content:
                # 先备份文件
                backup_path = self.backup_file(file_path)
                if not backup_path:
                    self.failed_files.append(str(file_path))
                    return False

                # 写入修改后的内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                self.processed_files.append((str(file_path), str(backup_path)))
                logger.info(f"已处理文件: {file_path}")
                return True
            return False

        except UnicodeDecodeError:
            logger.warning(f"无法解码文件（可能不是文本文件）: {file_path}")
            self.failed_files.append(str(file_path))
            return False
        except Exception as e:
            logger.error(f"处理文件时出错 {file_path}: {str(e)}")
            self.failed_files.append(str(file_path))
            return False

    def process_directory(self):
        """处理目标目录下的所有文件"""
        logger.info(f"开始处理目录: {self.target_dir}")

        # 创建新的备份目录
        self.backup_dir = self.target_dir / f"{self.backup_pattern}{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"备份目录已创建: {self.backup_dir}")

        # 遍历目录
        for root, dirs, files in os.walk(self.target_dir):
            # 过滤掉要排除的目录
            dirs[:] = [d for d in dirs if not self.should_exclude(Path(root) / d)]

            for file in files:
                file_path = Path(root) / file
                self.process_file(file_path)

        # 输出迁移总结
        logger.info("\n迁移总结:")
        logger.info(f"成功处理: {len(self.processed_files)} 个文件")
        logger.info(f"处理失败: {len(self.failed_files)} 个文件")

        if self.failed_files:
            logger.warning(f"失败的文件列表: {', '.join(self.failed_files)}")

        logger.info(f"备份文件位于: {self.backup_dir}")

    def rollback(self, backup_dir):
        """回滚到迁移前的状态"""
        if not backup_dir.exists():
            logger.error(f"备份目录不存在，无法回滚: {backup_dir}")
            return

        logger.info(f"开始从备份目录回滚: {backup_dir}")

        # 收集所有备份文件（排除迁移脚本）
        self.processed_files = []
        for root, _, files in os.walk(backup_dir):
            for file in files:
                # 跳过迁移脚本的备份
                if file == self.script_name:
                    continue

                backup_path = Path(root) / file
                rel_path = backup_path.relative_to(backup_dir)
                original_path = self.target_dir / rel_path
                if original_path.exists():
                    self.processed_files.append((str(original_path), str(backup_path)))

        # 执行回滚
        success_count = 0
        fail_count = 0

        for original_path, backup_path in self.processed_files:
            original_path = Path(original_path)
            backup_path = Path(backup_path)

            if backup_path.exists():
                try:
                    shutil.copy2(backup_path, original_path)
                    success_count += 1
                    logger.info(f"已回滚: {original_path}")
                except Exception as e:
                    fail_count += 1
                    logger.error(f"回滚失败 {original_path}: {str(e)}")
            else:
                fail_count += 1
                logger.warning(f"备份文件不存在，无法回滚: {backup_path}")

        logger.info("\n回滚总结:")
        logger.info(f"成功回滚: {success_count} 个文件")
        logger.info(f"回滚失败: {fail_count} 个文件")

        # 回滚完成后删除备份目录
        try:
            shutil.rmtree(backup_dir)
            logger.info(f"已删除备份目录: {backup_dir}")
        except Exception as e:
            logger.error(f"删除备份目录失败 {backup_dir}: {str(e)}")

    def auto_run(self):
        """自动检测并执行迁移或回滚"""
        # 查找最新的备份目录
        latest_backup = self.find_latest_backup()

        if latest_backup:
            logger.info(f"检测到存在备份目录: {latest_backup}")
            logger.info("将执行回滚操作...")
            self.rollback(latest_backup)
        else:
            logger.info("未检测到备份目录")
            logger.info("将执行迁移操作...")
            self.process_directory()


if __name__ == "__main__":
    # 项目目录设为当前目录（.）
    TARGET_DIRECTORY = "."
    # 要排除的目录（可选）
    EXCLUDE_DIRECTORIES = ["tests", "docs"]

    try:
        migrator = AutoPyQtMigrator(
            target_dir=TARGET_DIRECTORY,
            exclude_dirs=EXCLUDE_DIRECTORIES
        )
        migrator.auto_run()
    except Exception as e:
        logger.error(f"操作失败: {str(e)}", exc_info=True)
        exit(1)
