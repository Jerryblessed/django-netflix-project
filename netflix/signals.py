import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Movie, Movie2
import ffmpeg

@receiver(post_save, sender=Movie2)
def process_movie_resolutions(sender, instance, created, **kwargs):
    if created:
        original_path = instance.original_file.path
        resolutions = {
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "4k": (3840, 2160),
        }

        # Check original resolution
        probe = ffmpeg.probe(original_path)
        video_streams = [stream for stream in probe["streams"] if stream["codec_type"] == "video"]
        if not video_streams:
            raise ValueError("No video streams found in the file.")
        width = video_streams[0]["width"]
        height = video_streams[0]["height"]

        # Generate lower resolutions if possible
        for resolution, dimensions in resolutions.items():
            if width >= dimensions[0] and height >= dimensions[1]:
                output_path = f"{os.path.splitext(original_path)[0]}_{resolution}.mp4"
                ffmpeg.input(original_path).output(
                    output_path, vf=f"scale={dimensions[0]}:{dimensions[1]}"
                ).run()
                # Save the generated file to the appropriate field
                setattr(instance, f"resolution_{resolution}", output_path)
            else:
                if resolution == "720p":
                    print("The video resolution is too low for further reduction.")
                    break

        # Save the instance to update the file fields
        instance.save()
