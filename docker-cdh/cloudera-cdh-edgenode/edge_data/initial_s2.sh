#!/bin/bash

cp CentOS-163.repo /etc/yum.repos.d/
yum install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gcc make vim wget python-pip

pip install --upgrade pip
# wget https://www.python.org/ftp/python/3.6.2/Python-3.6.2.tar.xz
# tar -xvJf  Python-3.6.2.tar.xz
# cd Python-3.6.2
# ./configure prefix=/usr/local/python3
# make && make install
# 
# pip install virtualenv
# virtualenv -p /usr/local/python3/bin/python3 venv
# venv/bin/pip install jupyter

wget http://downloads.lightbend.com/scala/2.12.8/scala-2.12.8.rpm
yum install scala-2.12.8.rpm
SCALA_VERSION=2.12.8 ALMOND_VERSION=0.4.0
curl -Lo coursier https://git.io/coursier-cli
chmod a+x coursier
./coursier bootstrap -r jitpack -i user -I user:sh.almond:scala-kernel-api_2.12.8:0.4.0 sh.almond:scala-kernel_2.12.8:0.4.0 -o almond
./almond --install


pip install jupyter
jupyter notebook --generate-config
jupyter notebook --allow-root
