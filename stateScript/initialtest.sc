int cameraPin = 17 %current digitalOut pin of camera
int loopInterval = 2 %alternate camera input every 2ms. this means trigger intervals are 4ms long.
int count = 0 %placeholder variable to make sure that cam func while loop always runs
int camInterval = 5000
%trigger camera pulses
function 1
	%keep while loop always true so that camera is always acquiring at beginning of experiment
	while count < 1 do every loopInterval
		portout[cameraPin] = flip
	end
end
trigger(1);