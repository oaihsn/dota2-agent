package skadistats.clarity;

import skadistats.clarity.source.MappedFileSource;
import skadistats.clarity.processor.runner.SimpleRunner;
import skadistats.clarity.model.Entity;
import skadistats.clarity.model.*;
import java.util.*;

/**
 * Dota 2 demo parser - uses iteration over ticks.
 * This version manually walks through the demo ticks.
 */
public class DemoParser {
    
    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("Usage: java DemoParser <demo.dem>");
            System.exit(1);
        }
        
        String demoPath = args[0];
        System.out.println("PARSING: " + demoPath);
        
        var source = new MappedFileSource(demoPath);
        
        // Get tick count
        int lastTick = source.getLastTick();
        System.out.println("TOTAL_TICKS: " + lastTick);
        
        // Use for loop to iterate - SimpleRunner can iterate by tick
        var runner = new SimpleRunner(source);
        
        // We'll iterate manually using the source
        // First, let's just walk through and see tick by tick
        int interval = 30;
        int collected = 0;
        
        // Create a simple tick processor
        var processor = new SimpleTickCollector(interval);
        
        // Run with our processor
        runner.runWith(processor);
        
        var data = processor.getHeroData();
        System.out.println("TICKS_COLLECTED: " + processor.getTicksCollected());
        System.out.println("HERO_RECORDS: " + data.size());
        
        for (String record : data) {
            System.out.println("HERO:" + record);
        }
        
        System.out.println("DONE");
    }
    
    /**
     * Simple processor that collects hero data at intervals.
     */
    public static class SimpleTickCollector {
        private List<String> heroData = new ArrayList<>();
        private int interval;
        private int tickCount = 0;
        private int collected = 0;
        
        public SimpleTickCollector(int interval) {
            this.interval = interval;
        }
        
        // Clarity will call this for every tick
        public boolean onTickEnd(boolean synthetic) {
            tickCount++;
            
            if (tickCount % interval != 0) {
                return true;
            }
            
            // Need to get entities here somehow
            // But we don't have access without proper injection
            return true;
        }
        
        public List<String> getHeroData() {
            return heroData;
        }
        
        public int getTicksCollected() {
            return collected;
        }
    }
}