
ffmpeg:
	ffmpeg -framerate 24 -i sim/port_3/png_frames/frame_%05d.png -vf \
	"scale=1920:1080:force_original_aspect_ratio=decrease, pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \
	-pix_fmt yuv420p -r 24 -t 20 ../docs/field_mag.mp4
