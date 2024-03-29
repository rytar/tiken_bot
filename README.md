# 知見bot (tiken_bot)
[![MIT licensed][shield-license]](#)

[shield-license]: https://img.shields.io/badge/license-MIT-blue.svg

<p align="center">
    <img src="./tiken_bot_image.jpg" width="512" />
</p>

# Overview
The tiken_bot is a bot account on misskey.io.
For more information about the function of the bot, please visit [@tiken_bot@misskey.io](https://misskey.io/@tiken_bot).

# Environment
- Ubuntu 22.04
- Python 3.10
- Docker 24.0.4

# Dependencies
## Misskey API
An API token is required to use the Misskey API. The following two permissions are granted to the token.
- Compose or delete notes
- View your notifications

The issued token should be set in the `"TOKEN"` field in the `config.json` file.

## Python
```
$ pip install -r requirements.txt
```

## Redis
Redis is used to manage the notes that tiken_bot has already renoted and to avoid duplicate renotes.
```
$ sudo docker create --name redis-stack -p 6379:6379 redis/redis-stack:latest
```

## Elasticsearch
Elasticsearch is registered with the renoted notes and acts as an internal system for the search commands available in tiken_bot.
```
$ cd ~
$ wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.7.1-linux-x86_64.tar.gz
$ wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.7.1-linux-x86_64.tar.gz.sha512
$ shasum -a 512 -c elasticsearch-8.7.1-linux-x86_64.tar.gz.sha512
$ tar -xzf elasticsearch-8.7.1-linux-x86_64.tar.gz
$ cd ~/elasticsearch-8.7.1
$ ./bin/elasticsearch
```

After starting Elasticsearch, the Elasticsearch password will be displayed.
You can use Elasticsearch from the bot by setting this password in the `"ES_PASS"` field in the `config.json` file.

# How to launch
Run `$ source start.sh` to launch the bot.

# Author
misskey: [@Rytaryu@misskey.io](https://misskey.io/@Rytaryu)

# License
tiken_bot is licensed under the [MIT](./LICENSE) license.  
Copyright &copy; 2023, Rytaryu