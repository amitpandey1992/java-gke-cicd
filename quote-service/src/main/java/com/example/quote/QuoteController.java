package com.example.quote;

import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;
import java.util.Random;

@RestController
@RequestMapping("/api/quotes")
@CrossOrigin(origins = "*")
public class QuoteController {

    private final String[] QUOTES = {
        "First, solve the problem. Then, write the code. – John Johnson",
        "It’s not a bug – it’s an undocumented feature. – Anonymous",
        "Code is like humor. When you have to explain it, it’s bad. – Cory House",
        "Simplicity is the soul of efficiency. – Austin Freeman",
        "Make it work, make it right, make it fast. – Kent Beck",
        "Programmer: A machine that turns caffeine into code. – Anonymous",
        "Talk is cheap. Show me the code. – Linus Torvalds",
        "Software and cathedrals are much the same – first we build them, then we pray. – Anonymous"
    };

    private final Random random = new Random();

    @GetMapping
    public Map<String, String> getRandomQuote() {
        String quote = QUOTES[random.nextInt(QUOTES.length)];
        Map<String, String> response = new HashMap<>();
        response.put("quote", quote);
        return response;
    }
}
