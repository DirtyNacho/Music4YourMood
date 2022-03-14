from cgi import test
import random
from tkinter import *
from time import sleep
from tkinter.tix import MAX
from typing import Counter
import cv2
import numpy as np
import thread6 
from spotipy.oauth2 import SpotifyOAuth
import json
from json import JSONEncoder
import spotipy
from fer import FER
# import collections.Counter

access_token='BQDh7XH5J8hMJchaIF6kLlO3yDKcX82_N0'
client_id='7e053abf0bf142979b40007446972048'
client_secret='487c5dcfa72e4e379f9e40e9135a8dc8'
device_id='0d1841b0976bae2a3a310dd74c0f3df354899bc8'
# sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=client_id,client_secret=client_secret))
playlist4moods = {
    'neutral' : ['deep house' , 'todays top hits' , 'neutral' , 'everyday favourites'],
    'happy' : ['happy' , 'dance' , 'party' , 'great day'],
    'sad' : ['sad' , 'mood booster', 'chill','heartbroken'],
    'angry': ['angry' , 'rock this' , 'walk like a badass'],
    'fear': ['fear' , 'walk like a badass' ],
    'disgust': ['angry' , 'rock this' , 'sad','heartbroken'],
    'surprise' : ['todays top hits' , 'everyday favourites']
}

moodcounter = {
    'neutral' : 0,
    'happy' : 0,
    'sad' : 0,
    'angry': 0,
    'fear': 0
}


sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               redirect_uri='http://localhost:8888/callback',
                                               scope="streaming"))

songs2add = 3
songs_in_queue = 0
MAX_QUEUE_SIZE=5
ended = False
song_treshhold = 3
song_queue = []

#image taken after time_delta seconds to process
time_delta=20
picsbefload = 4 
started = True
emo_detector = FER(mtcnn=True)

def thread_func():

    global time_delta 
    global picsbefload  
    global started
    webcam = cv2.VideoCapture(0) #Use camera 0
    
    count = 0
    while True:
        (rval, im) = webcam.read()
        # test_image_one=cv2.flip(im,1,1) #Flip to act as a mirror
        
        # print(test_image_one)
        # cv2.imshow('PIC',im)
        Gathermood(im)
        
        if count == picsbefload or started == True:
            Search()  
            count = 0
        
        sleep(time_delta) 
        count = count + 1
        key = cv2.waitKey(10)
        
        if ended == True:
            print("Ended")
            break
        
    # Stop video
    webcam.release()

    # Close all started windows
    return 1
        

root=Tk()
root.geometry('1200x600')
root.resizable(0,0)
root.title('Spotify UI')
first_open=FALSE
result = 0
playing=FALSE
player=0

def Gathermood(test_image_one):    
    global moodcounter
    
    # dominant_emotion, emotion_score = emo_detector.top_emotion(test_image_one)
    captured_emotions = emo_detector.detect_emotions(test_image_one)
    
    if captured_emotions == []:
        return 
    
    a_counter=Counter(moodcounter)
    b_counter=Counter(captured_emotions[0]['emotions'])
    
    moodcounter = dict(a_counter+b_counter)
    print(moodcounter)
    return
 
    
    
def get_playlist():
    global moodcounter
    
    emotion_score = max(moodcounter.values())
    dominant_emotion = max(moodcounter, key=moodcounter.get)
    print(dominant_emotion,emotion_score) 
    
    moodcounter.update({
    'neutral' : 0,
    'happy' : 0,
    'sad' : 0,
    'angry': 0,
    'fear': 0
})
        
    if dominant_emotion == None:
        dominant_emotion = 'neutral'

    plist = playlist4moods[dominant_emotion][random.randint(0,len(playlist4moods[dominant_emotion])-1)]       #search a random playlist for the dominant emotion
         
    result= sp.search(plist,type='playlist')
    response = {
        'playlist_name': ' ',
        'tracks': [],
        'mood' : []
        }
    response['mood']=[dominant_emotion, emotion_score]
    # response['playlist_name'] = result['playlists']['items'][random.randint(0,res_count-1)]           #random searched playlist
    response['playlist_name'] = result['playlists']['items'][0]   #first searched playlist
    response['tracks'] = sp.playlist(response['playlist_name']['id'])
    return response
    

def AddSongs():
    
    global song_queue
    global songs_in_queue
    global started
    
    print("Adding songs")
    if songs_in_queue == 0 :
        return 

    countsong = songs2add
    if started == True:
        countsong = MAX_QUEUE_SIZE
        started = False
    
    count = 0 
    while count< countsong:
        sp.add_to_queue(song_queue[0]['track']['uri'])
        song_queue.pop(0)
        songs_in_queue=songs_in_queue-1
        count = count + 1 
    
    RefreshListbox()

def Search():
    
    global result
    global song_queue
    global songs_in_queue
    print("Searching")
    result = get_playlist()
    #get a sample of MAX_QUEUE_SIZE from the playlit
    songs=random.sample(list(result['tracks']['tracks']['items']),MAX_QUEUE_SIZE)
    songs_in_queue = MAX_QUEUE_SIZE
    
    #Add the resulted song to a queue 
    for song in songs:
        song['mood']=result['mood'][0]
        song['playlist'] = result['playlist_name']['name']
        song_queue.append(song)
        
    RefreshListbox()
    AddSongs()
    
        
#Function to Get Selected Value
def Selected():
    if select.curselection(): 
        return int(select.curselection()[0])
    else: 
        return -1
    
    
def RefreshListbox():
    #Print the song queue to a listbox
    
    global song_queue
    global result
    
    select.delete(0,END)
    # result2 = json.loads(get_playlist2(playlist['id']))
    select.insert(END,result['playlist_name']['name'])
    select.insert(END,'---------------')
    
    count = 1 
    for song in song_queue:
        item = song['track']['name']+ " - "+ song['track']['artists'][0]['name'] + " -> " + song['mood'] + " - " + song['playlist']
        select.insert(END,item)
        if count <= song_treshhold+1:
            select.itemconfig(count+1, {'bg':'red'})
        
        count=count+1
    
    
#play first song from the listbox  
def Play():
    global song_queue 
    global songs_in_queue
    
    # for s in song_queue[0]['track']:
    #     print(s)
    
    sp.add_to_queue(song_queue[0]['track']['uri'])
    uri_list=[]
    uri_list=uri_list.append(song_queue[0]['track']['uri'])
    # print(song_queue[0]['track']['uri'])
    # print(sp.devices())
    sp.start_playback(device_id=sp.devices(),uris=uri_list)
    song_queue.pop(0)
    songs_in_queue=songs_in_queue-1
    RefreshListbox()
    

    
Label(root,text="Spotify UI",font=("Helvetica",20,"bold")).place(x=200,y=50)
mood = Label(root,text='MOOD',font="12").place(x=150,y=150)

Label(root,text='Tracks',font="12").place(x=750,y=50)
frame = Frame(root)
frame.place(x=600,y=100)

Button(root,text="Play Track",cursor="hand2",command=Play).place(x=950,y=540)


scroll = Scrollbar(frame,orient=VERTICAL)
select = Listbox(frame,yscrollcommand=scroll.set,height=15,width=70)
scroll.config(command=select.yview)
scroll.pack(side=RIGHT,fill=Y)
# select.place(x=650,y=100)
select.pack(side=LEFT,fill=BOTH,expand=1)


result = thread6.run_threaded(thread_func)
root.mainloop()
ended = True 