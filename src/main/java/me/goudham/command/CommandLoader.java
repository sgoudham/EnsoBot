package me.goudham.command;

import java.lang.reflect.Method;
import java.util.List;
import java.util.Map;
import net.dv8tion.jda.api.interactions.commands.build.CommandData;
import net.dv8tion.jda.internal.utils.tuple.Pair;

public interface CommandLoader {
    List<CommandData> loadIntoMapAndReturnCommands(Map<String, Pair<Object, Method>> commandMap);
}
