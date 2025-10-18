#!/bin/sh
# Packaging and Release (基于 Poetry 构建)

# 使用 Docker 环境执行构建和测试
docker run --workdir=$(pwd)/ --volume="/home/$USER:/home/$USER" tzutalin/py2qt4 /bin/sh -c '
    make qt4py2;
    make test;
    poetry build --format sdist;
    poetry install --no-dev
'

while true; do
    read -p "Do you wish to deploy this to PyPI (twine upload dist/* or pip install dist/*)?" yn
    case $yn in
        [Yy]* )
            # 进入 Docker 环境执行发布（使用 Poetry 或 twine）
            docker run -it --rm --workdir=$(pwd)/ --volume="/home/$USER:/home/$USER" tzutalin/py2qt4 /bin/sh -c '
                # 可选：用 Poetry 直接发布（需提前配置 PyPI 凭据）
                # poetry publish --username __token__ --password <your-token>
                # 或使用 twine 发布（兼容现有习惯）
                twine upload dist/*
            ';
            break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

# 测试安装命令（基于 Poetry 构建的包）
# pip install dist/labelimg-2.0.1.6.tar.gz