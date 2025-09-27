#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtCore import (QFile, QIODevice, QTextStream, QLocale,
                            QStringConverter)


class StringBundle:
    __create_key = object()

    __bundle_cache = {}

    @classmethod
    def get_bundle(cls, locale_str=None):
        if locale_str is None:
            locale = QLocale.system()
            locale_str = f"{locale.name()}"

        cache_key = locale_str
        if cache_key in cls.__bundle_cache:
            return cls.__bundle_cache[cache_key]

        bundle = StringBundle(cls.__create_key, locale_str)
        cls.__bundle_cache[cache_key] = bundle
        return bundle

    def __init__(self, create_key, locale_str):
        assert create_key == StringBundle.__create_key, \
            "StringBundle objects must be created using StringBundle.get_bundle()"

        self.__strings = {}
        self.__locale = locale_str

        # 尝试加载特定语言的资源文件
        base_name = "i18n/strings"
        attempted_paths = []

        # 优先先尝试完整语言代码（如zh_CN）
        path = f"{base_name}_{locale_str}.properties"
        attempted_paths.append(path)
        if self.__load_bundle(path):
            return

        # 尝试语言代码的主要部分（如zh）
        if '_' in locale_str:
            lang_code = locale_str.split('_')[0]
            path = f"{base_name}_{lang_code}.properties"
            attempted_paths.append(path)
            if self.__load_bundle(path):
                return

        # 加载默认资源文件
        path = f"{base_name}.properties"
        attempted_paths.append(path)
        if self.__load_bundle(path):
            return

        # 如果所有尝试都失败，记录警告但不抛出异常
        print(f"Warning: Could not load string bundle from any of: {attempted_paths}")

    def __load_bundle(self, path):
        file = QFile(path)
        if not file.exists():
            return False

        if not file.open(QIODevice.ReadOnly | QIODevice.Text):
            return False

        # 在PySide6中，使用QStringConverter.Encoding枚举值设置编码
        text_stream = QTextStream(file)
        # 使用正确的枚举类型设置UTF-8编码
        text_stream.setEncoding(QStringConverter.Encoding.Utf8)

        while not text_stream.atEnd():
            line = text_stream.readLine().strip()
            if not line or line.startswith('#'):
                continue

            separator_index = line.find('=')
            if separator_index <= 0:
                continue

            key = line[:separator_index].strip()
            value = line[separator_index + 1:].strip()
            self.__strings[key] = value

        file.close()
        return True

    def get_string(self, key, default=None):
        return self.__strings.get(key, default if default is not None else key)
