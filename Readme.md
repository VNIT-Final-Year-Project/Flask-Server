##For installing requried packages
```
pip install -r requirements.txt
pip install Audio-0.3-py3-none-any.whl
```

##Install docker for database
```
docker pull tarundecipher/audio-mongo
docker run -p 27017:27017 audio-mongo
```

##Open Music_wav directory in terminal and execute following commands

```
npm install http-server
http-server --cors=*
```
