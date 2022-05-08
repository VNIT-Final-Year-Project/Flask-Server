
import os
dirname = os.getcwd()

from flask import Flask
from flask import request
from flask_cors import CORS, cross_origin
import librosa
import subprocess
import soundfile as sf

from Audio.AudioMain import Audio
from Audio.SyncAlgorithms.correlationSyncNoFilter import correlationSyncNoFilter
from Audio.FingerprintAlgorithms.invariantAlgorithm import invariantAlgorithm
from Audio.database.mongodb_database import mongodb_database
from multiprocessing import Pool
from Audio.Paths import Paths
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/',methods=['GET','POST'])
@cross_origin()
def index():
    if(request.method=='POST'):
        print('request came')

        f = open(os.path.join(dirname, 'Music_wav\\file.wav'), 'wb')
        f.write(request.data)
        f.close()
        subprocess.call(['ffmpeg','-y', '-i', os.path.join(dirname, 'Music_wav\\file.wav'),
                         os.path.join(dirname, 'Music_wav\\file_output.wav')],shell=True)

        x, sr = librosa.load(os.path.join(dirname, 'Music_wav\\file.wav'), sr=48000)
        y = librosa.resample(x, 48000, 44100)
        sf.write(os.path.join(dirname, 'Music_wav\\file.wav'),y,44100)
        Paths.getInstance().setRecordingPath(os.path.join(dirname, 'Music_wav\\final_file.wav'))
        #
        audio = Audio(correlationSyncNoFilter(), invariantAlgorithm(),
                      mongodb_database("mongodb://localhost:27017",
                                       r'final_file.wav'),
                      os.path.join(dirname, 'Music_wav\\{}')
                      )
        result, songs_found = audio.result_from_database()
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        db = client['Fingerprints']
        collection_song = db['SongIds']

        """Using Single Machine multiple cores"""
        p2 = Pool()
        data = []
        for i in range(1, len(result)):
            data.append((result[i], result[0]))
        output = p2.starmap(audio.lcs, data)
        print(len(result[0]))

        p2.close()
        p2.join()
        print(max(output))
        SongName = collection_song.find_one({'_id': songs_found[output.index(max(output))]})['SongName']
        print(SongName)
        client.close()

        return SongName



@app.route('/sync', methods=['GET','POST'])
@cross_origin()
def sync():

    if (request.method == 'POST'):
        print('request came')
        Paths.getInstance().setRecordingPath(os.path.join(dirname, 'Music_wav\\final_file.wav'))
        songName = request.form.get('song')
        print(songName)
        file = request.files['blob']
        file.save(os.path.join(dirname, 'Music_wav\\file.wav'))
        subprocess.call(['ffmpeg', '-y', '-i', os.path.join(dirname, 'Music_wav\\file.wav'),
                         os.path.join(dirname, 'Music_wav\\final_file.wav')], shell=True)

        x, sr = librosa.load(os.path.join(dirname, 'Music_wav\\file.wav'), sr=48000)
        y = librosa.resample(x, 48000, 44100)
        sf.write(os.path.join(dirname, 'Music_wav\\final_file.wav'), y, 44100)
        audio = Audio(correlationSyncNoFilter(), invariantAlgorithm(),
                      mongodb_database("mongodb://localhost:27017",
                                       r'final_file.wav'),
                      os.path.join(dirname, 'Music_wav\\{}')
                      )
        return {"syncPoint":audio.sync_audio(songName,False)}



if __name__=="__main__":
    app.run(debug=True,host='0.0.0.0',port=5000)