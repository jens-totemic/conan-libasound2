#include <stdio.h>
#include <stdlib.h>
#include <alsa/asoundlib.h>

int main() {
	int i;
	int err;
	short buf[128];
	snd_pcm_t *playback_handle;
	snd_pcm_hw_params_t *hw_params;

	if ((err = snd_pcm_open (&playback_handle, argv[1], SND_PCM_STREAM_PLAYBACK, 0)) < 0) {
		fprintf (stderr, "cannot open audio device %s (%s)\n", 
			 argv[1],
			 snd_strerror (err));
		exit (1);
	}
	snd_pcm_close (playback_handle);
    return EXIT_SUCCESS;
}
