# -*- coding: utf-8 -*-
"""Тест JPype2 с clarity-protobuf"""
import jpype

jvm_path = "C:/Program Files/Java/jdk-17/bin/server/jvm.dll"
jars = [
    "lib/clarity-protobuf-4.8.jar",
    "lib/clarity.jar",
    "lib/clarity-2.7.0.jar",
    "lib/clarity-3.0.0.jar"
]

print("Starting JVM...")
jpype.startJVM(jvm_path, "-ea", convertStrings=True, classpath=jars)
print("JVM started!")

# Пробуем разные классы
classes_to_try = [
    "skadistats.clarity.wire.shared.demo.proto.Demo$CDemoFileInfo",
    "skadistats.clarity.wire.s2.S2Packet",
    "skadistats.clarity.processor.runner.Runner",
    "com.skadistats.clarity.Clarity",
]

for cls_name in classes_to_try:
    try:
        cls = jpype.JClass(cls_name)
        print(f"✅ Found: {cls_name}")
    except Exception as e:
        print(f"❌ Not found: {cls_name} - {str(e)[:50]}")

print("\nDone!")