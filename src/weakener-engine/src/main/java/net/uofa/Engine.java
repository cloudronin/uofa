package net.uofa;

import net.uofa.oos.OOSEngine;

import java.util.Arrays;

/**
 * UofA engine dispatcher — single fat JAR entry point.
 *
 * Inspects the first CLI argument and dispatches to the matching subcommand.
 * If the first argument doesn't match a known subcommand, all arguments pass
 * through to {@link WeakenerEngine} unchanged. This preserves backward
 * compatibility with the existing {@code commands/rules.py:run_structured}
 * invocation pattern (which passes {@code <input.jsonld> --rules ... --context ...}
 * with no leading subcommand keyword).
 *
 * Subcommands:
 *   weakener        → {@link WeakenerEngine} (also the default when no subcommand matches)
 *   oos             → {@link net.uofa.oos.OOSEngine}
 *   substrate-test  → {@link OOSSubstrateTest}
 *
 * Help/version forwarded to the dispatched subcommand. The dispatcher itself
 * does not parse {@code --help} or {@code --version} — those reach the chosen
 * picocli subcommand which knows what to print.
 */
public final class Engine {

    private Engine() {}

    public static void main(String[] args) {
        if (args.length > 0) {
            switch (args[0]) {
                case "oos":
                    OOSEngine.main(stripFirst(args));
                    return;
                case "substrate-test":
                    OOSSubstrateTest.main(stripFirst(args));
                    return;
                case "weakener":
                    WeakenerEngine.main(stripFirst(args));
                    return;
                default:
                    // fall through — unknown first arg, pass everything to WeakenerEngine
            }
        }
        WeakenerEngine.main(args);
    }

    private static String[] stripFirst(String[] args) {
        return Arrays.copyOfRange(args, 1, args.length);
    }
}
