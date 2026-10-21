package net.kasax.tamagotchi.pet;

/**
 * One-shot animations. The server starts them with {@link TamaPet#playAction} which broadcasts an
 * entity event; the client keeps the start tick and the animator plays the clip.
 */
public enum PetAction {
    PETTED(36),
    EAT(40),
    ATTACK(12),
    BREATH(22),
    TALENT(34),
    FEED_OWNER(26),
    CELEBRATE(26),
    SNIFF(34),
    POUNCE(14),
    SHAKE(36),
    SCRATCH(40),
    YAWN(30),
    TAMED(44),
    BOUNCE(12),
    COUGH(26),
    LOOK_UP(36),
    GROOMED(30),
    PLAY(24);

    /** Entity event ids 100..(100+n); vanilla stays well below 100. */
    public static final int EVENT_BASE = 100;

    public final int length;

    PetAction(int length) {
        this.length = length;
    }

    public byte eventId() {
        return (byte) (EVENT_BASE + ordinal());
    }

    public static PetAction byEvent(byte id) {
        int i = id - EVENT_BASE;
        return i >= 0 && i < values().length ? values()[i] : null;
    }
}
