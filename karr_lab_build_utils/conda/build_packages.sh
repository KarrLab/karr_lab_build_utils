#!/bin/bash

# Builds packages for distribution via anaconda.org
#
# @author Jonathan Karr, karr@mssm.edu
# @date 2016-11-09

conda_src=https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
conda_path=~/miniconda3
arch=linux-64
versions=( 2.7.12 3.5.2 )
cur_dir=$(pwd)
this_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
requirements_file_apt=$this_dir/requirements.apt.txt
requirements_file_pip=$this_dir/requirements.pip.txt
anaconda_organization_file=$this_dir/tokens/ANACONDA_ORGANIZATION
anaconda_username_file=$this_dir/tokens/ANACONDA_USERNAME
anaconda_password_file=$this_dir/tokens/ANACONDA_PASSWORD
copy_owner_packages=( anaconda/numpy anaconda/scipy anaconda/pip anaconda/wheel )
conda_skeletons_dir=$this_dir/skeletons

#install other packages
sudo apt-get install -y $(cat $requirements_file_apt)
sudo apt-get upgrade -y $(cat $requirements_file_apt)
if [ ! -f /usr/local/lib/libgit2.so ]; then
    mkdir -p ~/tmp
    cd ~/tmp
    wget https://github.com/libgit2/libgit2/archive/v0.24.3.tar.gz -O libgit2-0.24.3.tar.gz
    tar -xvvf libgit2-0.24.3.tar.gz
    cd libgit2-0.24.3
    cmake .
    make
    sudo make install
    sudo ldconfig
fi

#install conda
if [ ! -f $conda_path/bin/conda ]
then
    mkdir -p ~/tmp
    wget $conda_src -O ~/tmp/conda.sh
    bash ~/tmp/conda.sh -b
fi

#update conda
$conda_path/bin/conda upgrade -y conda

#install and update conda-build
$conda_path/bin/conda install -y conda-build
$conda_path/bin/conda upgrade -y conda-build

#install anaconda client
$conda_path/bin/conda install -y anaconda-client
$conda_path/bin/conda upgrade -y anaconda-client

#install python    
for version in "${versions[@]}"
do
    if [ ! -d $conda_path/envs/$version ]
    then
        $conda_path/bin/conda create -n $version python=$version -y
    fi
done

#install pip packages
for version in "${versions[@]}"
do
    version_major_minor=$(expr match $version '\([0-9]*\.[0-9]*\)\.[0-9]*$')
    touch $conda_path/envs/$version/lib/python${version_major_minor}/site-packages/easy-install.pth
    source $conda_path/bin/activate $version
    pip install -U setuptools

    for owner_package in "${copy_owner_packages[@]}"
    do
        package=$(echo $owner_package | cut -d"/" -f2)
        readarray package_info < <($conda_path/bin/anaconda show $owner_package | grep "+")
        pkg_ver=$(echo ${package_info[-1]} | cut -d" " -f2)
        pip install $package==$pkg_ver
    done

    pip install -U -r $requirements_file_pip #todo use github api to collect requirements directly from packages
    source $conda_path/bin/deactivate
done

#anaconda login
anaconda_username=$(<$anaconda_username_file)
anaconda_password=$(<$anaconda_password_file)
anaconda_organization=$(<$anaconda_organization_file)
$conda_path/bin/anaconda logout
$conda_path/bin/anaconda login --username $anaconda_username --password $anaconda_password

#remove old package versions so new ones can be uploaded
readarray package_infos < <($conda_path/bin/anaconda show karrlab | grep $arch)
for package_info in "${package_infos[@]}"
do
    organization_package=$(echo $package_info | cut -d" " -f1)
    $conda_path/bin/anaconda remove --force $organization_package
done

#copy numpy, scipy, pip, wheels
for owner_package in "${copy_owner_packages[@]}"
do
    readarray package_info < <($conda_path/bin/anaconda show $owner_package | grep "+")
    pkg_ver=$(echo ${package_info[-1]} | cut -d" " -f2)
    $conda_path/bin/anaconda copy $owner_package/$pkg_ver --to-owner $anaconda_organization
done

#build and upload pip packages
$conda_path/bin/conda config --set anaconda_upload yes

mkdir -p $conda_skeletons_dir
cd $conda_skeletons_dir
for version in "${versions[@]}"
do    
    version_major_minor=$(expr match $version '\([0-9]*\.[0-9]*\)\.[0-9]*$')
    version_major_minor_nodot=${version_major_minor/\./}
    source $conda_path/bin/activate $version

    readarray package_infos < <(pip freeze)
    rm -rf ./*    
    for package_info in "${package_infos[@]}"
    do
        package=$(echo $package_info | cut -d"=" -f1)
        pkg_ver=$(echo $package_info | cut -d"=" -f3)

        err=$($conda_path/bin/conda skeleton pypi --version $pkg_ver $package 2>&1 > /dev/null)
        if [[ ! -z $err ]]
        then
            package_underscore=${package//\-/_}
            err=$($conda_path/bin/conda skeleton pypi --version $pkg_ver $package_underscore 2>&1 > /dev/null)
            if [[ ! -z $err ]]
            then
                echo "Unable to create skeleton: $err" 1>&2
                exit 1
            fi
        fi
    done

    for package_info in "${package_infos[@]}"
    do
        package=$(echo $package_info | cut -d"=" -f1)
        pkg_ver=$(echo $package_info | cut -d"=" -f3)

        if [ ! -d $package ]
        then
            package=${package//\-/_}
        fi

        if [[ -z $($conda_path/bin/anaconda show karrlab/${package}/${pkg_ver}/${arch}/${package}-${pkg_ver}-py${version_major_minor_nodot}_0.tar.bz2) ]]
        then
            $conda_path/bin/conda build --no-test --user $anaconda_organization --python $version_major_minor $package
        fi
    done

    source $conda_path/bin/deactivate
done
cd $cur_dir
