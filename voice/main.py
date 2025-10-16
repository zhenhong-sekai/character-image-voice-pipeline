#!/usr/bin/env python3
"""
MP4 Audio Transcription Script using AssemblyAI API

This script transcribes audio from MP4 files using the AssemblyAI API.
It supports both local file upload and direct URL processing.
"""

import requests
import time
import os
import sys
import subprocess
import json
from pathlib import Path
from openai import OpenAI


class AssemblyAITranscriber:
    def __init__(self, api_key):
        """Initialize the transcriber with API key."""
        self.base_url = "https://api.assemblyai.com"
        self.headers = {
            "authorization": "70702281c18e427f8093e5f5385a3195"
        }
    
    def upload_file(self, file_path):
        """Upload a local file to AssemblyAI and return the upload URL."""
        print(f"Uploading file: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "rb") as f:
            response = requests.post(
                self.base_url + "/v2/upload",
                headers=self.headers,
                data=f
            )
        
        if response.status_code != 200:
            raise RuntimeError(f"Upload failed: {response.status_code} - {response.text}")
        
        upload_url = response.json()["upload_url"]
        print(f"File uploaded successfully. URL: {upload_url}")
        return upload_url
    
    def start_transcription(self, audio_url, speech_model="universal", speaker_labels=True):
        """Start transcription job and return transcript ID."""
        print("Starting transcription...")
        
        data = {
            "audio_url": audio_url,
            "speech_model": speech_model,
            "speaker_labels": speaker_labels
        }
        
        url = self.base_url + "/v2/transcript"
        response = requests.post(url, json=data, headers=self.headers)
        
        if response.status_code != 200:
            raise RuntimeError(f"Transcription request failed: {response.status_code} - {response.text}")
        
        transcript_id = response.json()['id']
        print(f"Transcription started. ID: {transcript_id}")
        return transcript_id
    
    def poll_transcription(self, transcript_id, max_wait_time=300):
        """Poll for transcription completion and return the result."""
        polling_endpoint = self.base_url + "/v2/transcript/" + transcript_id
        start_time = time.time()
        
        print("Polling for transcription completion...")
        
        while True:
            if time.time() - start_time > max_wait_time:
                raise RuntimeError("Transcription timeout exceeded")
            
            response = requests.get(polling_endpoint, headers=self.headers)
            
            if response.status_code != 200:
                raise RuntimeError(f"Polling failed: {response.status_code} - {response.text}")
            
            transcription_result = response.json()
            status = transcription_result['status']
            
            print(f"Status: {status}")
            
            if status == 'completed':
                print("Transcription completed!")
                return transcription_result
            
            elif status == 'error':
                error_msg = transcription_result.get('error', 'Unknown error')
                raise RuntimeError(f"Transcription failed: {error_msg}")
            
            else:
                print("Still processing... waiting 3 seconds")
                time.sleep(3)
    
    def transcribe_file(self, file_path, speech_model="universal", max_wait_time=300):
        """Complete transcription workflow for a local file."""
        try:
            # Upload file
            audio_url = self.upload_file(file_path)
            
            # Start transcription
            transcript_id = self.start_transcription(audio_url, speech_model)
            
            # Poll for completion
            transcription_result = self.poll_transcription(transcript_id, max_wait_time)
            
            return transcription_result
            
        except Exception as e:
            print(f"Error during transcription: {str(e)}")
            raise
    
    def transcribe_url(self, audio_url, speech_model="universal", max_wait_time=300):
        """Complete transcription workflow for a URL."""
        try:
            # Start transcription
            transcript_id = self.start_transcription(audio_url, speech_model)
            
            # Poll for completion
            transcription_result = self.poll_transcription(transcript_id, max_wait_time)
            
            return transcription_result
            
        except Exception as e:
            print(f"Error during transcription: {str(e)}")
            raise


class TargetSpeakerIdentifier:
    def __init__(self):
        """Initialize the LLM client for speaker identification."""
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "your_openai_api_key_here"),
            base_url="https://yunwu.ai/v1",
        )
    
    def identify_target_speaker(self, utterances, target_speaker_description):
        """Use LLM to identify which speaker segments belong to the target speaker."""
        print(f"Using LLM to identify target speaker: {target_speaker_description}")
        
        # Prepare the conversation data for the LLM
        conversation_text = ""
        for utterance in utterances:
            speaker = utterance.get('speaker', 'Unknown')
            text = utterance.get('text', '')
            conversation_text += f"Speaker {speaker}: {text}\n"
        
        # Create the prompt for the LLM
        prompt = f"""
        I have a conversation transcript with multiple speakers. I need you to identify which speaker (A, B, C, etc.) matches my target speaker description.

        CONVERSATION:
        {conversation_text}

        TARGET SPEAKER DESCRIPTION: {target_speaker_description}

        Please analyze the conversation and tell me which speaker label (A, B, C, etc.) best matches the target speaker description. 
        Respond with ONLY the speaker label (e.g., "A" or "B" or "C") and nothing else.
        If you cannot determine which speaker matches, respond with "UNKNOWN".
        """
        
        try:
            completion = self.client.chat.completions.create(
                model="gemini-2.5-flash-nothinking",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            identified_speaker = completion.choices[0].message.content.strip()
            print(f"LLM identified target speaker as: {identified_speaker}")
            return identified_speaker
            
        except Exception as e:
            print(f"Error in LLM identification: {str(e)}")
            return "UNKNOWN"
    
    def filter_target_speaker_segments(self, utterances, target_speaker):
        """Filter utterances to return only segments from the target speaker."""
        target_segments = []
        
        for utterance in utterances:
            speaker = utterance.get('speaker', 'Unknown')
            if speaker == target_speaker:
                target_segments.append(utterance)
        
        return target_segments


class VideoSegmentExtractor:
    def __init__(self):
        """Initialize the video segment extractor."""
        self.ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Check if FFmpeg is available on the system."""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            print("FFmpeg is available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Warning: FFmpeg not found. Video extraction will not be available.")
            print("Please install FFmpeg: https://ffmpeg.org/download.html")
            return False
    
    def _format_timestamp(self, milliseconds):
        """Convert milliseconds to HH:MM:SS.mmm format."""
        seconds = milliseconds / 1000
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def extract_target_speaker_segments(self, target_segments, input_video_path, output_path="target_speaker_segments.mp4"):
        """Extract video segments where the target speaker is speaking."""
        if not self.ffmpeg_available:
            print("Cannot extract video segments: FFmpeg not available")
            return False
        
        if not target_segments:
            print("No target speaker segments to extract")
            return False
        
        print(f"Extracting {len(target_segments)} target speaker segments...")
        
        # Create filter complex for FFmpeg
        filter_parts = []
        concat_parts = []
        
        for i, segment in enumerate(target_segments):
            start_time = segment.get('start', 0)
            end_time = segment.get('end', start_time + 1000)  # Default 1 second if no end time
            
            start_formatted = self._format_timestamp(start_time)
            duration = (end_time - start_time) / 1000  # Convert to seconds
            
            # Add segment to filter
            filter_parts.append(f"[0:v]trim=start={start_time/1000}:duration={duration},setpts=PTS-STARTPTS[v{i}]")
            filter_parts.append(f"[0:a]atrim=start={start_time/1000}:duration={duration},asetpts=PTS-STARTPTS[a{i}]")
            concat_parts.append(f"[v{i}][a{i}]")
        
        # Create filter complex
        filter_complex = ";".join(filter_parts) + ";" + "".join(concat_parts) + f"concat=n={len(target_segments)}:v=1:a=1[outv][outa]"
        
        # FFmpeg command
        cmd = [
            'ffmpeg', '-i', input_video_path,
            '-filter_complex', filter_complex,
            '-map', '[outv]', '-map', '[outa]',
            '-c:v', 'libx264', '-c:a', 'aac',
            '-y',  # Overwrite output file
            output_path
        ]
        
        try:
            print(f"Running FFmpeg command to extract segments...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"Successfully extracted target speaker segments to: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e}")
            print(f"FFmpeg stderr: {e.stderr}")
            return False
    
    def extract_individual_segments(self, target_segments, input_video_path, output_dir="target_speaker_segments"):
        """Extract each target speaker segment as a separate file."""
        if not self.ffmpeg_available:
            print("Cannot extract video segments: FFmpeg not available")
            return False
        
        if not target_segments:
            print("No target speaker segments to extract")
            return False
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Extracting {len(target_segments)} individual segments...")
        
        for i, segment in enumerate(target_segments):
            start_time = segment.get('start', 0)
            end_time = segment.get('end', start_time + 1000)
            
            start_formatted = self._format_timestamp(start_time)
            end_formatted = self._format_timestamp(end_time)
            
            output_file = os.path.join(output_dir, f"segment_{i+1:03d}_{start_formatted.replace(':', '-')}.mp4")
            
            # FFmpeg command for individual segment
            cmd = [
                'ffmpeg', '-i', input_video_path,
                '-ss', start_formatted,
                '-to', end_formatted,
                '-c', 'copy',  # Copy without re-encoding for speed
                '-y',  # Overwrite output file
                output_file
            ]
            
            try:
                print(f"Extracting segment {i+1}/{len(target_segments)}: {start_formatted} - {end_formatted}")
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(f"  -> {output_file}")
            except subprocess.CalledProcessError as e:
                print(f"Error extracting segment {i+1}: {e}")
                continue
        
        print(f"Individual segments saved to: {output_dir}")
        return True


def main():
    """Main function to transcribe MP4 files with hardcoded settings."""
    
    # ===== CONFIGURATION - EDIT THESE SETTINGS =====
    MP4_FILE_NAME = "videoplayback.mp4"  # Change this to your MP4 file name
    SPEECH_MODEL = "universal"        # Options: "universal", "best", "nano"
    SAVE_TO_FILE = True               # Set to True to save transcript to file
    OUTPUT_FILE = "transcript.txt"    # Output file name
    MAX_WAIT_TIME = 300              # Maximum wait time in seconds
    
    # TARGET SPEAKER CONFIGURATION
    TARGET_SPEAKER_DESCRIPTION = "Donald Trump"  # Describe your target speaker
    USE_LLM_IDENTIFICATION = True    # Set to True to use LLM for speaker identification
    
    # VIDEO EXTRACTION CONFIGURATION
    EXTRACT_VIDEO_SEGMENTS = True    # Set to True to extract video segments
    EXTRACTION_MODE = "combined"     # Options: "combined" (single file) or "individual" (separate files)
    OUTPUT_VIDEO_FILE = "target_speaker_segments.mp4"  # Output file for combined segments
    OUTPUT_VIDEO_DIR = "target_speaker_segments"      # Directory for individual segments
    # ================================================
    
    # Initialize transcriber
    transcriber = AssemblyAITranscriber("70702281c18e427f8093e5f5385a3195")
    
    try:
        # Check if it's a URL or local file
        if MP4_FILE_NAME.startswith(('http://', 'https://')):
            print(f"Transcribing URL: {MP4_FILE_NAME}")
            transcription_result = transcriber.transcribe_url(
                MP4_FILE_NAME, 
                SPEECH_MODEL, 
                MAX_WAIT_TIME
            )
        else:
            # Check if file exists in mp4_files folder
            file_path = os.path.join("mp4_files", MP4_FILE_NAME)
            if not os.path.exists(file_path):
                print(f"Error: File not found: {file_path}")
                print("Please place your MP4 file in the 'mp4_files' folder")
                print("And update the MP4_FILE_NAME variable in the script")
                sys.exit(1)
            
            print(f"Transcribing file: {file_path}")
            transcription_result = transcriber.transcribe_file(
                file_path, 
                SPEECH_MODEL, 
                MAX_WAIT_TIME
            )
        
        # Display results with speaker diarization
        print("\n" + "="*50)
        print("TRANSCRIPTION RESULT WITH SPEAKER DIARIZATION:")
        print("="*50)
        
        # Get the full transcript text
        transcript_text = transcription_result.get('text', '')
        print(f"Full Transcript:\n{transcript_text}\n")
        
        # Display speaker-separated utterances
        utterances = transcription_result.get('utterances', [])
        if utterances:
            print("All Speaker-Separated Transcription:")
            print("-" * 50)
            for utterance in utterances:
                speaker = utterance.get('speaker', 'Unknown')
                text = utterance.get('text', '')
                print(f"Speaker {speaker}: {text}")
            
            # LLM-based target speaker identification
            if USE_LLM_IDENTIFICATION:
                print("\n" + "="*50)
                print("TARGET SPEAKER IDENTIFICATION:")
                print("="*50)
                
                # Initialize LLM identifier
                speaker_identifier = TargetSpeakerIdentifier()
                
                # Identify target speaker using LLM
                identified_speaker = speaker_identifier.identify_target_speaker(
                    utterances, TARGET_SPEAKER_DESCRIPTION
                )
                
                if identified_speaker != "UNKNOWN":
                    print(f"Target speaker identified as: Speaker {identified_speaker}")
                    
                    # Filter and display only target speaker segments
                    target_segments = speaker_identifier.filter_target_speaker_segments(
                        utterances, identified_speaker
                    )
                    
                    if target_segments:
                        print(f"\nTARGET SPEAKER SEGMENTS ({TARGET_SPEAKER_DESCRIPTION}):")
                        print("-" * 50)
                        target_text = ""
                        for segment in target_segments:
                            text = segment.get('text', '')
                            start_time = segment.get('start', 0)
                            end_time = segment.get('end', start_time + 1000)
                            print(f"Speaker {identified_speaker}: {text}")
                            print(f"  Time: {start_time/1000:.1f}s - {end_time/1000:.1f}s")
                            target_text += text + " "
                        
                        print(f"\nComplete target speaker transcript:")
                        print(f"'{target_text.strip()}'")
                        
                        # Extract video segments if enabled
                        if EXTRACT_VIDEO_SEGMENTS:
                            print("\n" + "="*50)
                            print("EXTRACTING VIDEO SEGMENTS:")
                            print("="*50)
                            
                            video_extractor = VideoSegmentExtractor()
                            
                            if not video_extractor.ffmpeg_available:
                                print("FFmpeg not available. Generating manual extraction instructions...")
                                print("Run: python extract_segments_manual.py")
                                print("This will create FFmpeg commands for manual extraction.")
                            else:
                                if EXTRACTION_MODE == "combined":
                                    # Extract all segments into one file
                                    input_video_path = os.path.join("mp4_files", MP4_FILE_NAME)
                                    success = video_extractor.extract_target_speaker_segments(
                                        target_segments, input_video_path, OUTPUT_VIDEO_FILE
                                    )
                                    if success:
                                        print(f"Combined video segments saved to: {OUTPUT_VIDEO_FILE}")
                                
                                elif EXTRACTION_MODE == "individual":
                                    # Extract each segment as separate file
                                    input_video_path = os.path.join("mp4_files", MP4_FILE_NAME)
                                    success = video_extractor.extract_individual_segments(
                                        target_segments, input_video_path, OUTPUT_VIDEO_DIR
                                    )
                                    if success:
                                        print(f"Individual video segments saved to: {OUTPUT_VIDEO_DIR}/")
                    else:
                        print("No segments found for the identified target speaker")
                else:
                    print("Could not identify target speaker")
        else:
            print("No speaker diarization data available")
        
        print("="*50)
        
        # Save to file if requested
        if SAVE_TO_FILE:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write("FULL TRANSCRIPT:\n")
                f.write("="*50 + "\n")
                f.write(transcript_text + "\n\n")
                
                if utterances:
                    f.write("ALL SPEAKER-SEPARATED TRANSCRIPT:\n")
                    f.write("="*50 + "\n")
                    for utterance in utterances:
                        speaker = utterance.get('speaker', 'Unknown')
                        text = utterance.get('text', '')
                        f.write(f"Speaker {speaker}: {text}\n")
                    
                    # Add target speaker segments if LLM identification was used
                    if USE_LLM_IDENTIFICATION and 'identified_speaker' in locals() and identified_speaker != "UNKNOWN":
                        f.write(f"\nTARGET SPEAKER SEGMENTS ({TARGET_SPEAKER_DESCRIPTION}):\n")
                        f.write("="*50 + "\n")
                        target_text = ""
                        for segment in target_segments:
                            text = segment.get('text', '')
                            f.write(f"Speaker {identified_speaker}: {text}\n")
                            target_text += text + " "
                        
                        f.write(f"\nCOMPLETE TARGET SPEAKER TRANSCRIPT:\n")
                        f.write("="*50 + "\n")
                        f.write(f"'{target_text.strip()}'\n")
            
            print(f"\nTranscription saved to: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
