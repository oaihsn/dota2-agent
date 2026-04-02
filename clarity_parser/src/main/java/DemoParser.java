import com.skadistats.clarity.Clarity;
import com.skadistats.clarity.model.*;
import com.skadistats.clarity.processor.*;
import com.skadistats.clarity.processor.entities.*;
import com.skadistats.clarity.processor.stringtables.*;
import com.skadistats.clarity.source.*;
import org.slf4j.*;
import java.io.*;
import java.util.*;

public class DemoParser {
    private static final Logger log = LoggerFactory.getLogger(DemoParser.class);
    private static final int INTERVAL_TICKS = 30;
    
    private static List<String> outputLines = new ArrayList<>();
    
    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("Usage: java -jar demo-parser.jar <demo_file>");
            System.exit(1);
        }
        
        String demoFile = args[0];
        System.out.println("Parsing: " + demoFile);
        
        try {
            Source source = new FileSource(new File(demoFile));
            Clarity clarity = new Clarity(source);
            
            final int[] lastTick = {0};
            
            clarity.run(new Processor[]{
                new OnTick(30) {
                    public void tick(int tick) {
                        if (tick <= lastTick[0]) return;
                        lastTick[0] = tick;
                        processTick(tick);
                    }
                }
            });
            
        } catch (Exception e) {
            System.err.println("ERROR:" + e.getMessage());
            e.printStackTrace();
        }
        
        // Выводим все собранные данные
        for (String line : outputLines) {
            System.out.println(line);
        }
    }
    
    private static void processTick(int tick) {
        // Данные собираются через entity callbacks
    }
}
