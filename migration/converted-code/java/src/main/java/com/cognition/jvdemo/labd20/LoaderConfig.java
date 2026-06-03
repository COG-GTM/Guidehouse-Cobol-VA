package com.cognition.jvdemo.labd20;

import java.nio.file.Path;

/**
 * Configuration for a LABD20 run. Port of the {@code LoaderConfig} dataclass.
 * {@code sectionForCount} defaults to "MA" (LABD20.pco:400).
 */
public record LoaderConfig(
        Path cardPath,
        Path commentPath,
        boolean truncateAfterProcessing,
        String sectionForCount) {

    public LoaderConfig(Path cardPath, Path commentPath) {
        this(cardPath, commentPath, true, "MA");
    }

    public LoaderConfig(Path cardPath, Path commentPath, boolean truncateAfterProcessing) {
        this(cardPath, commentPath, truncateAfterProcessing, "MA");
    }
}
