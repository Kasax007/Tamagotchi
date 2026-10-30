package net.kasax.tamagotchi.film;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.resources.sounds.Sound;
import net.minecraft.client.resources.sounds.SoundInstance;
import net.minecraft.world.phys.Vec3;

/**
 * The film's sound track. The film client has no sound device, so every sound the game starts while a shot is
 * filmed (see {@code SoundLogMixin}) is written to {@code <shot>/sounds.jsonl}: when (seconds of the shot), which
 * file, its volume and pitch, where it played and where the camera was. The video tools mix the real sound files
 * from that, so the footage sounds the way the game does.
 */
public final class FilmSound {
    private static final List<String> LINES = new ArrayList<>();
    private static volatile boolean recording;
    private static long startMillis;
    private static Path dir;
    private static int fps, frames;

    private FilmSound() {
    }

    /**
     * Starts the log of a shot whose first frame is at film time {@code millis}. {@code fps}: frames per second of
     * game time (30 plays in real time, 10 is a time-lapse); times in the log are seconds of game time.
     */
    public static synchronized void begin(Path shotDir, long millis, int shotFps, int shotFrames) {
        LINES.clear();
        dir = shotDir;
        startMillis = millis;
        fps = shotFps;
        frames = shotFrames;
        recording = true;
    }

    /** Ends the log and writes it next to the frames. */
    public static synchronized void end() {
        recording = false;
        try {
            Files.write(dir.resolve("sounds.jsonl"), LINES);
            Files.writeString(dir.resolve("shot.json"), String.format(Locale.ROOT, "{\"fps\":%d,\"frames\":%d}%n", fps, frames));
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
        FilmDirector.LOG.info("[Film] {} sounds in {}", LINES.size(), dir.getFileName());
        LINES.clear();
    }

    /** Client thread: a sound is about to start. */
    public static void log(SoundInstance instance) {
        if (!recording) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        if (instance.getOrResolve(mc.getSoundManager()) == null) {
            return;
        }
        Sound sound = instance.getSound();
        if (sound == null || sound.getPath() == null) {
            return;
        }
        Camera cam = mc.gameRenderer.mainCamera();
        Vec3 c = cam.position();
        float volume = instance.getVolume();
        double t = (FilmClock.millis() - startMillis) / 1000.0;
        String line = String.format(Locale.ROOT,
                "{\"t\":%.3f,\"event\":\"%s\",\"file\":\"%s\",\"source\":\"%s\",\"volume\":%.3f,\"pitch\":%.3f,"
                        + "\"x\":%.3f,\"y\":%.3f,\"z\":%.3f,\"relative\":%b,\"attenuation\":\"%s\",\"distance\":%.2f,"
                        + "\"stream\":%b,\"cam_x\":%.3f,\"cam_y\":%.3f,\"cam_z\":%.3f,\"cam_yaw\":%.2f,\"cam_pitch\":%.2f}",
                t, instance.getIdentifier(), sound.getPath(), instance.getSource().getName(), volume, instance.getPitch(),
                instance.getX(), instance.getY(), instance.getZ(), instance.isRelative(), instance.getAttenuation(),
                sound.getAttenuationDistance(volume), sound.shouldStream(), c.x, c.y, c.z, cam.yRot(), cam.xRot());
        synchronized (FilmSound.class) {
            if (recording) {
                LINES.add(line);
            }
        }
    }
}
