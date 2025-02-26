#!/bin/bash
# direnvのインストール方法（Ubuntu/Debian）
# sudo apt-get update
# sudo apt-get install -y direnv

# direnvのインストール方法（Amazon Linux 2023）
sudo dnf install -y direnv

# direnvのインストール方法（macOS）
# brew install direnv

# シェル設定ファイルに direnv hook を追加
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
# ZSHを使用している場合
# echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc

# 設定を反映
source ~/.bashrc
# または
# source ~/.zshrc

# .envrcファイルを許可
direnv allow . 