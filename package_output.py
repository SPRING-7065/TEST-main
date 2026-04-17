import shutil
import os
import sys
import datetime

folder_name = 'WebAutoDownloader'
dist_dir = os.path.join('dist', folder_name)

if not os.path.exists(dist_dir):
    print('Cannot find output folder. dist contents:')
    if os.path.exists('dist'):
        print(os.listdir('dist'))
    sys.exit(1)

print(f"Output folder: {dist_dir}")

src = 'browser'
dst = os.path.join(dist_dir, 'browser')

if not os.path.exists(src):
    print("Error: browser directory not found")
    sys.exit(1)

if os.path.exists(dst):
    shutil.rmtree(dst)

print("Copying Chromium...")
shutil.copytree(src, dst)
print("Done.")

date_str = datetime.date.today().strftime('%Y%m%d')
zip_name = f'WebAutoDownloader_v1.1.2_{date_str}'
shutil.make_archive(zip_name, 'zip', 'dist', folder_name)

size = os.path.getsize(zip_name + '.zip') / 1024 / 1024
print(f"Package ready: {zip_name}.zip ({size:.1f} MB)")
