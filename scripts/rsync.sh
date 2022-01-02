ls -al /
ls -al /worlds-volume-dev
echo "Rsyncing..."
rsync -arP /plugins-volume-dev/ /plugins-data
rsync -arP /worlds-volume-dev/ /worlds-data
