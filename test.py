from pytube import YouTube

YouTube('https://youtu.be/2lAe1cqCOXo').streams.first().download()