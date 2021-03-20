import subprocess
import time

rc = 1

while rc not in [0, 2]:
    child = subprocess.Popen('net stop DiscordDheadsBot', stdout=subprocess.PIPE)
    streamdata = child.communicate()[0]
    rc = child.returncode
    if rc == 0:
        time.sleep(5)

rc = 1

while rc not in [0, 2]:
    child = subprocess.Popen('net start DiscordDheadsBot', stdout=subprocess.PIPE)
    streamdata = child.communicate()[0]
    rc = child.returncode
