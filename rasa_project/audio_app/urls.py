from django.urls import path
from . import views

urlpatterns = [
    path('check-hash-audio/',views.CheckAndSaveAudioHash.as_view(),name='check_hash_audio'),
    #path('fingerprint/', views.FingerPrintAudio.as_view(), name='audio_fingerprint'),
    #path('recognise_audio/',views.CheckAudioFingerprint.as_view(),name='recognise_audio')
]