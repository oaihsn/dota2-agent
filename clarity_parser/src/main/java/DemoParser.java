import com.skadistats.clarity.Clarity;
import com.skadistats.clarity.model.*;
import com.skadistats.clarity.processor.*;
import com.skadistats.clarity.processor.entities.*;
import com.skadistats.clarity.processor.stringtables.*;
import com.skadistats.clarity.source.*;
import org.slf4j.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class DemoParser {
    private static final Logger log = LoggerFactory.getLogger(DemoParser.class);
    private static final int INTERVAL_TICKS = 30;
    
    // Выходной файл
    private static PrintWriter outputWriter;
    private static String outputFile;
    
    // Счётчик тиков
    private static AtomicInteger tickCounter = new AtomicInteger(0);
    
    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("Usage: java -jar demo-parser.jar <demo_file> [output_json]");
            System.exit(1);
        }
        
        String demoFile = args[0];
        outputFile = args.length > 1 ? args[1] : "output.json";
        
        System.out.println("Parsing: " + demoFile);
        System.out.println("Output: " + outputFile);
        
        try {
            outputWriter = new PrintWriter(new FileWriter(outputFile));
            outputWriter.println("[");  // Начало массива
            
            Source source = new FileSource(new File(demoFile));
            Clarity clarity = new Clarity(source);
            
            final int[] lastTick = {0};
            final boolean[] firstRecord = {true};
            
            clarity.run(new Processor[]{
                new OnTick(INTERVAL_TICKS) {
                    public void tick(int tick) {
                        if (tick <= lastTick[0]) return;
                        lastTick[0] = tick;
                        
                        String record = processTick(tick, clarity);
                        if (record != null) {
                            if (!firstRecord[0]) {
                                outputWriter.println(",");
                            }
                            outputWriter.print(record);
                            firstRecord[0] = false;
                        }
                    }
                }
            });
            
            outputWriter.println("\n]");  // Конец массива
            outputWriter.close();
            
            System.out.println("Done! Total ticks processed: " + tickCounter.get());
            
        } catch (Exception e) {
            System.err.println("ERROR: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    private static String processTick(int tick, Clarity clarity) {
        StringBuilder sb = new StringBuilder();
        boolean firstPlayer = true;
        
        // Получаем всех игроков
        List<Entity> players = new ArrayList<>();
        
        for (Entity e : clarity.getEntities().getAll()) {
            String className = e.getDtClass().getName();
            
            // Игроки (DT_DOTA_Unit_Hero_...)
            if (className != null && className.startsWith("CDOTA_Unit_Hero_")) {
                players.add(e);
            }
        }
        
        // Если нет игроков, пропускаем
        if (players.isEmpty()) {
            return null;
        }
        
        tickCounter.incrementAndGet();
        
        // Формируем JSON запись
        sb.append("  {\n");
        sb.append("    \"tick\": ").append(tick).append(",\n");
        sb.append("    \"players\": [\n");
        
        for (Entity player : players) {
            if (!firstPlayer) {
                sb.append(",\n");
            }
            firstPlayer = false;
            
            sb.append("      {\n");
            
            // Hero ID
            int heroId = getIntProperty(player, "m_iHeroID");
            sb.append("        \"hero_id\": ").append(heroId).append(",\n");
            
            // Позиция
            float x = getFloatProperty(player, "m_vecOrigin[0]");
            float y = getFloatProperty(player, "m_vecOrigin[1]");
            sb.append("        \"pos_x\": ").append(String.format("%.2f", x)).append(",\n");
            sb.append("        \"pos_y\": ").append(String.format("%.2f", y)).append(",\n");
            
            // HP
            int health = getIntProperty(player, "m_iHealth");
            int maxHealth = getIntProperty(player, "m_iMaxHealth");
            sb.append("        \"health\": ").append(health).append(",\n");
            sb.append("        \"max_health\": ").append(maxHealth).append(",\n");
            
            // Mana
            int mana = getIntProperty(player, "m_flMana");
            int maxMana = getIntProperty(player, "m_flMaxMana");
            sb.append("        \"mana\": ").append(mana).append(",\n");
            sb.append("        \"max_mana\": ").append(maxMana).append(",\n");
            
            // Level
            int level = getIntProperty(player, "m_nLevel");
            sb.append("        \"level\": ").append(level).append(",\n");
            
            // Gold
            int gold = getIntProperty(player, "m_iGold");
            sb.append("        \"gold\": ").append(gold).append(",\n");
            
            // Net Worth
            int netWorth = getIntProperty(player, "m_iNetWorth");
            sb.append("        \"net_worth\": ").append(netWorth).append(",\n");
            
            // Player Slot (0-4 для Radiant, 128-132 для Dire)
            int playerSlot = getIntProperty(player, "m_iPlayerID");
            sb.append("        \"player_slot\": ").append(playerSlot).append(",\n");
            
            // Team
            int team = getIntProperty(player, "m_iTeamNum");
            sb.append("        \"team\": ").append(team).append(",\n");
            
            // Inventory - ищем предметы
            sb.append("        \"inventory\": [");
            boolean firstItem = true;
            for (int i = 0; i < 6; i++) {
                String itemProp = "m_hItems[" + i + "]";
                int itemId = getIntProperty(player, itemProp);
                if (itemId > 0) {
                    if (!firstItem) sb.append(", ");
                    sb.append(itemId);
                    firstItem = false;
                }
            }
            sb.append("],\n");
            
            // Abilities - ищем способности
            sb.append("        \"abilities\": {");
            boolean firstAbility = true;
            for (int i = 0; i < 24; i++) {
                String abilityProp = "m_hAbilities[" + i + "]";
                int abilityId = getIntProperty(player, abilityProp);
                if (abilityId > 0) {
                    if (!firstAbility) sb.append(", ");
                    sb.append("\"").append(abilityId).append("\": ").append(i + 1);
                    firstAbility = false;
                }
            }
            sb.append("},\n");
            
            // Last action - ищем последнее действие
            // m_nLastActionTick - последний тик действия
            int lastActionTick = getIntProperty(player, "m_nLastActionTick");
            sb.append("        \"last_action_tick\": ").append(lastActionTick);
            
            sb.append("\n      }");
        }
        
        sb.append("\n    ]\n");
        sb.append("  }");
        
        return sb.toString();
    }
    
    private static int getIntProperty(Entity e, String propName) {
        try {
            Property property = e.getProperty(propName);
            if (property != null) {
                return property.getValue() != null ? (Integer) property.getValue() : 0;
            }
        } catch (Exception ex) {
            // Игнорируем
        }
        return 0;
    }
    
    private static float getFloatProperty(Entity e, String propName) {
        try {
            Property property = e.getProperty(propName);
            if (property != null) {
                return property.getValue() != null ? (Float) property.getValue() : 0.0f;
            }
        } catch (Exception ex) {
            // Игнорируем
        }
        return 0.0f;
    }
}
