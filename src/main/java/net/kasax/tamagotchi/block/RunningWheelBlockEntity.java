package net.kasax.tamagotchi.block;

import net.kasax.tamagotchi.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Only exists so the wheel can be drawn spinning; the spin itself is client-side. */
public class RunningWheelBlockEntity extends BlockEntity {
    public long lastRun;
    /** Client: current angle and speed so the wheel speeds up and coasts to a stop. */
    public float angle;
    public float speed;
    public long lastFrameTick = -1;

    public RunningWheelBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.RUNNING_WHEEL_BE, pos, state);
    }
}
