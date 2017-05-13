# Create a new forked environment

```
# fork off "mynewenv" cluster desired-state config
git branch --track mynewenv master
git checkout mynewenv
git pull # pulls updates from master branch into mynewenv branch
<use future script to copy vault items from /secret/landscaper/master to /secret/landscaper/mynewenv>
make deploy
```
