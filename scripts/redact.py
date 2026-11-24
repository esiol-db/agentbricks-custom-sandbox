"""Blur rectangular regions (e.g. emails) in a PNG or video with ffmpeg.

Usage: python redact.py <in> <out> x:y:w:h [x:y:w:h ...] [--speed 2] [--gif]
"""
import subprocess
import sys

args = sys.argv[1:]
src, dst = args[0], args[1]
speed = float(args[args.index("--speed") + 1]) if "--speed" in args else 1.0
gif = "--gif" in args
regions = [a for a in args[2:] if a.count(":") == 3]

chain, last = [], "0:v"
for i, r in enumerate(regions):
    x, y, w, h = r.split(":")
    chain.append(f"[{last}]split[s{i}a][s{i}b];[s{i}b]crop={w}:{h}:{x}:{y},boxblur={min(12, int(h) // 2 - 1)}:3:{max(1, min(6, int(h) // 4 - 1))}:3[b{i}];"
                 f"[s{i}a][b{i}]overlay={x}:{y}[o{i}]")
    last = f"o{i}"
fc = ";".join(chain) if chain else "[0:v]null[o]"
if not chain:
    last = "o"
is_video = src.endswith((".webm", ".mp4"))
if is_video and gif:
    fc += (f";[{last}]setpts=PTS/{speed},fps=8,scale=1100:-1:flags=lanczos,split[g1][g2];"
           "[g1]palettegen=max_colors=128[p];[g2][p]paletteuse=dither=bayer:bayer_scale=4[out]")
elif is_video:
    fc += f";[{last}]setpts=PTS/{speed},fps=30,format=yuv420p[out]"
else:
    fc += f";[{last}]null[out]"
cmd = ["ffmpeg", "-y", "-v", "error", "-i", src, "-filter_complex", fc, "-map", "[out]"]
if is_video and not gif:
    cmd += ["-c:v", "libx264", "-crf", "22", "-preset", "slow", "-movflags", "+faststart", "-an"]
subprocess.run(cmd + [dst], check=True)
print("wrote", dst)
