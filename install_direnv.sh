#!/bin/bash

# Homebrewのインストールに必要なパッケージをインストール
sudo dnf install -y git curl file procps

# Homebrewをインストール
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Homebrewの環境変数を設定
echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

# Homebrewの動作確認
brew doctor

# direnvのインストール
brew install direnv

# direnvの設定をシェルに追加
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc

# 設定を反映
source ~/.bashrc

# .envrcファイルがなければサンプルからコピー
if [ ! -f .envrc ]; then
  if [ -f .envrc.example ]; then
    cp .envrc.example .envrc
    echo "Created .envrc from example file. Please edit it with your actual IP addresses."
  else
    echo 'export ALLOWED_IPS="0.0.0.0/0"' > .envrc
    echo "Created default .envrc file. Please edit it with your actual IP addresses."
  fi
fi

# .envrcファイルを許可
direnv allow .

echo "Homebrew and direnv installation complete."
echo "Please restart your shell or run 'source ~/.bashrc' to apply changes."
echo "Edit .envrc file to set your allowed IP addresses." 