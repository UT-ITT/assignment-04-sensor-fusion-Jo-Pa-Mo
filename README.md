[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/AktWbCri)
# assignment-04-CV-Sensor-Fusion

As always a virtual environment was used and the needed requirements are located in the ``requirements.txt``. Each file can be executed by pressing the "playbutton" in the top right of VS-Code or by command, depending on the code solution one can also add arguments like an input path.

## Perspective Transformation

Execute this script via "playbutton" or via command. One can select 4 points for the warping by clicking somewhere with the left mousebutton, by clicking ESC the script is reset, by clicking S the image is saved and by clicking Q the programm is quit.

**Possible arguments:**

Specify an input path: <br>
``python .\perspective_transformation\image_extractor.py --input-path .\perspective_transformation\rickroll.png``

Specify an output path: <br>
``python .\perspective_transformation\image_extractor.py --output-path .\sensor_fusion\output.png``<br>
(Here you must also specify a filename!)

Specify the output resolution: <br>
``python .\perspective_transformation\image_extractor.py --x-resolution 1000 --y-resolution 500`` <br>(If you only specify x- or y-resolution, the default is used for the other one, so please be aware of that!)

## AR Game

The game extracts the region between markers and warps the image so it always displays a perfect rectangle. In theory it should adjust to any webcam resolution, though i could not test it because i only have one webcam available. It tracks your fingertip coming from any direction, the important part here is that the aruco markers are not obstructed and the hand must either come from the top, bottom, left or right. Entering your hand in a diagonal can lead to problems in theory but then usually an aruco marker is obstructed. In the case of aruco marker obstruction the last successful warping is stored and displayed, this is the reason why the game "freezes". This is a descision by choice, because otherwise the image warping would snap to the normal webcam view, which i found very annoying.

The game is quite simple, just use your finger to hit the targets on the screen as fast as possible to get the highest score possible in 30 seconds. You can press SPACE in the starting screen to start (or restart) the game, you can press R to reset the game to the starting screen or press Q to quit. 

My highscore is 44 so id like some feedback with your highscore! ^^

## Sensor Fusion

The sensor fusion code tracks the 5 aruco markers, split up into the one for the prediction and the 4 others for the border definitions. It then takes the center coordinate and the data from the accelerometer to display a predition depending the alpha value and the scaling factor. The alpha value can be increase by clicking the RIGHT_ARROW and decreased by clicking the LEFT_ARROW. In case you need to adjust the scaling factor, this can be done in the code. The center of the moving aruco marker is displayed in red, the predeiction is displayed in green.
The prediction can be reset by clicking button 1 in dippid. I recommend installing the aruco marker on the touchscreen side of the phone so one can press the 1 button anytime without flipping the phone.

To quite the program you can press Q at any time. 

Alpha was limited to the range [0, 1] because an alpha below zero or above one just makes no sense and leads to unexpected / crazy outputs that are uncontrollable.

**Paragraph on Implementation and different Alpha values:** <br>
Implementing the complementary filter provided a demonstration of sensosor fusion, that balances the strengths and weaknesses of the webcam and the accelerometer. The camera provides a stable feed of reference points for the marker position, but with some latency and lowe update rates. The accelerometer offers very fast and smooth updates but in this implementation not optimally since it is bound to the on_draw() funtion that updates the pyglet window. So in this implementation this sensor_fusion is not implemented optimally. The integration of the accelerometer data can improve the quality of tracking, since we have in theory one faster source of truth but it can also introduce some drift, that gets very extreme depending on the alpha value and scaling factor. An alpa value close to 1.0 forces the prediction to rely very heavily on the camera, resulting pretty much in a tracking that reflects the ground truth from the camera. An alpha value closer to 0.0 heavily trusts the accelerometer, this can yield a high responsiveness, but the lower the alpha value the higher the drift gets. You can try this out yourself by running the script and adjusting the alpha value to e.g. 0.1 or 0.2. An intermediate alpah of e.g 0.5 yields a good balance where we have a good responsiveness from the accelerometer whil still having a reliably results due to the reliability of the camera "pull" to the correct location.
