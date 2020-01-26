import pygame
import time
import RPi.GPIO as GPIO
import time

pygame.init()

def find_distance():
    try:
          GPIO.setmode(GPIO.BOARD)

          left_trigger = 7
          left_echo = 11
          right_trigger = 13
          right_echo = 15

          GPIO.setup(left_trigger, GPIO.OUT)
          GPIO.setup(left_echo, GPIO.IN)
          GPIO.output(left_trigger, GPIO.LOW)
          GPIO.setup(right_trigger, GPIO.OUT)
          GPIO.setup(right_echo, GPIO.IN)
          GPIO.output(right_trigger, GPIO.LOW)


          time.sleep(0.1)

          GPIO.output(left_trigger, GPIO.HIGH)
          time.sleep(0.00001)
          GPIO.output(left_trigger, GPIO.LOW)
          while GPIO.input(left_echo)==0:
                pulse_start_time = time.time()
          while GPIO.input(left_echo)==1:
                pulse_end_time = time.time()

          GPIO.output(right_trigger, GPIO.HIGH)
          time.sleep(0.00001)
          GPIO.output(right_trigger, GPIO.LOW)
          while GPIO.input(right_echo)==0:
                pulse_start_time_right = time.time()
          while GPIO.input(right_echo)==1:
                pulse_end_time_right = time.time()

          pulse_duration = pulse_end_time - pulse_start_time
          distance_left = round(pulse_duration * 17150, 2)
          print ("Distance_Left:", distance_left, "cm")
          pulse_duration_right = pulse_end_time_right - pulse_start_time_right
          distance_right = round(pulse_duration_right * 17150, 2)
          print ("Distance_Right:", distance_right, "cm")


          sound_left = pygame.mixer.Sound("left_back.wav")
          sound_right = pygame.mixer.Sound("right_back.wav")

          if distance_left < 10 and distance_right < 10:
              sound_left.play()
              sound_right.play()
              time.sleep(0.7)

          elif distance_left < 10:
              sound_left.play()
              time.sleep(0.7)

          elif distance_right < 10:
              sound_right.play()
              time.sleep(0.7)


    finally:
          GPIO.cleanup()



while True:
    find_distance()
