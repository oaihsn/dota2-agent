import requests
import os

# Create lib directory if not exists
os.makedirs('lib', exist_ok=True)

# Download JARs from Maven Central
jars = [
    ('https://repo1.maven.org/maven2/com/skadistats/clarity/3.1.1/clarity-3.1.1.jar', 'clarity-3.1.1.jar'),
    ('https://repo1.maven.org/maven2/com/google/protobuf/protobuf-java/3.19.4/protobuf-java-3.19.4.jar', 'protobuf-3.19.4.jar'),
    ('https://repo1.maven.org/maven2/it/unimi/dsi/fastutil/8.5.9/fastutil-8.5.9.jar', 'fastutil-8.5.9.jar'),
    ('https://repo1.maven.org/maven2/org/slf4j/slf4j-api/1.7.36/slf4j-api-1.7.36.jar', 'slf4j-api-1.7.36.jar'),
    # Fixed versions
    ('https://repo1.maven.org/maven2/io/github/classindex/classindex/3.10/classindex-3.10.jar', 'classindex-3.10.jar'),
    ('https://repo1.maven.org/maven2/org/xerial/snappy-java/1.1.8.2/snappy-java-1.1.8.2.jar', 'snappy-java-1.1.8.2.jar'),
]

for url, filename in jars:
    print(f"Downloading {filename}...")
    r = requests.get(url)
    if r.status_code == 200:
        with open(f'lib/{filename}', 'wb') as f:
            f.write(r.content)
        print(f"  OK: {len(r.content)} bytes")
    else:
        print(f"  FAILED: {r.status_code}")

print("\nDone!")