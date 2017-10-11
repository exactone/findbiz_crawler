echo '=============='
echo 'SSL authentication, manual enter needed'
echo '=============='
mkdir ~/ssl
#openssl genrsa -des3 -out ~/ssl/bonzoyang.key 1024 
#openssl req -new -key ~/ssl/bonzoyang.key -out  ~/ssl/bonzoyang.req
#sudo openssl x509 -req -days 7305 -sha1 -extfile /etc/ssl/openssl.cnf -extensions v3_ca -signkey ~/ssl/bonzoyang.key -in ~/ssl/bonzoyang.req -out /etc/ssl/certs/bonzoyang.crt
cd ~/ssl
#openssl req -x509 -newkey rsa:2048 -keyout ~/ssl/key.pem -out ~/ssl/cert.pem -days 7230
openssl req -x509 -nodes -days 3650 -newkey rsa:1024 -keyout ~/ssl/mykey.key -out ~/ssl/mycert.pem
cd ~


echo '=============='
echo 'install performance surveillance'
echo '=============='
mkdir ~/download
sudo apt-get install -y htop
sudo apt-get install -y p7zip-full

echo '=============='
echo 'install anaconda'
echo '=============='
wget -t0 -c -P ~/download https://repo.continuum.io/archive/Anaconda3-5.0.0-Linux-x86_64.sh
#anaconda_installer=`ls ~/download/Anaconda*x86_64.sh`
#chmod 755 $anaconda_installer
#$anaconda_installer -b -p ~/anaconda3
chmod 755 ~/download/Anaconda*x86_64.sh
~/download/Anaconda3-5.0.0-Linux-x86_64.sh -b -p ~/anaconda3
echo "export PATH=\"\$HOME/anaconda3/bin:\$PATH\"" >> ~/.bashrc
export PATH="$HOME/anaconda3/bin:$PATH"
#source ~/.bashrc


#echo '=============='
#echo 'install google api'
#echo '=============='
#sudo apt-get -y install --upgrade python-pip
#pip install --upgrade pip
#pip install --upgrade google-api-python-client


echo '=============='
echo 'set jupyter notebook server'
echo '=============='
echo "y" | jupyter notebook --generate-config
sedhome=$(echo $HOME | sed 's/\//\\\//g')
sed -i "s/#c.NotebookApp.certfile = ''/c.NotebookApp.certfile = '$sedhome\/ssl\/mycert.pem'/g"  ~/.jupyter/jupyter_notebook_config.py 
sed -i "s/#c.NotebookApp.keyfile = ''/c.NotebookApp.keyfile = '$sedhome\/ssl\/mykey.key'/g"  ~/.jupyter/jupyter_notebook_config.py
sed -i "s/#c.NotebookApp.ip = 'localhost'/c.NotebookApp.ip = '\*'/g"  ~/.jupyter/jupyter_notebook_config.py


touch get_sha_passwd.py
echo "from IPython.lib import passwd" >> get_sha_passwd.py
echo "print(passwd())" >> get_sha_passwd.py
sha1passwd=`python get_sha_passwd.py`
rm -f get_sha_passwd.py
sed -i "s/#c.NotebookApp.password = ''/c.NotebookApp.password = u'$sha1passwd'/g" ~/.jupyter/jupyter_notebook_config.py 
sed -i "s/#c.NotebookApp.open_browser = True/c.NotebookApp.open_browser = False/g" ~/.jupyter/jupyter_notebook_config.py
sed -i "s/#c.NotebookApp.port = 8888/c.NotebookApp.port = 9999/g" ~/.jupyter/jupyter_notebook_config.py

echo '=============='
echo 'install fake_useragent, selenium, '
echo '=============='
source ~/.bashrc
yes | conda create --name crawler anaconda
source activate crawler
pip install fake_useragent
pip install -U selenium


echo '=============='
echo 'install phantomjs'
echo '=============='
sudo apt-get update
sudo apt-get install build-essential chrpath libssl-dev libxft-dev -y
sudo apt-get install libfreetype6 libfreetype6-dev -y
sudo apt-get install libfontconfig1 libfontconfig1-dev -y
cd ~
export PHANTOM_JS="phantomjs-2.1.1-linux-x86_64"
wget https://github.com/Medium/phantomjs/releases/download/v2.1.1/$PHANTOM_JS.tar.bz2
sudo tar xvjf $PHANTOM_JS.tar.bz2
sudo mv $PHANTOM_JS /usr/local/share
sudo ln -sf /usr/local/share/$PHANTOM_JS/bin/phantomjs /usr/local/bin

source deactivate
