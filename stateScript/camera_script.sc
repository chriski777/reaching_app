int cameraPin = 1 %current digitalOut pin of camera
int loopInterval =  5 %Trigger interval of 5ms. Make sure this is larger than the exposure time of the camera.
int count = 0 %placeholder variable to make sure that cam func while loop always runs
int numLoops = 10000 % number of trigger intervals; 
int serialSig = 0 % 0 if serialization signal from port 2 is off, 1 if serialization signal from port 1 is on 

%Serialization Signals
callback portin[2] up
	serialSig = 1
end

callback portin[2] down
	serialSig = 0
end

%Function 1 trigger camera pulses
function 1
	updates off 1
	%total time of function 1 is numLoops * loopInterval ms 
	while count < numLoops do every loopInterval
		if (serialSig == 0) do 
			portout[cameraPin] = 1
			%keep pulse on for 1ms and then turn off pulse.
			do in 1
				portout[cameraPin] = 0
			end
			count = count + 1
		end
	end
end

trigger(1);
