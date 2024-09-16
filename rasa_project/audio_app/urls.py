from django.urls import path
from . import views


urlpatterns = [
    #path('check-hash-audio/',views.CheckAndSaveAudioHash.as_view(),name='check_hash_audio'),
    path('signed-aws-url/', views.GetSignedUrl.as_view(),name='signed_aws_url'),
    path('check-if-audio-hash/', views.CheckIfAudioHashExist.as_view(),name='check_if_audio_hash_exist'),
    path('save-audio-hash/', views.StoreAudioDetailsHashAndS3Key.as_view(),name='save_audio_hash'),
    #path('fingerprint/', views.FingerPrintAudio.as_view(), name='audio_fingerprint'),
    #path('recognise_audio/',views.CheckAudioFingerprint.as_view(),name='recognise_audio')
]