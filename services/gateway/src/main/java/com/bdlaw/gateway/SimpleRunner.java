package com.bdlaw.gateway;

import org.springframework.boot.SpringApplication;

public class SimpleRunner {
    public static void main(String[] args) {
        System.setProperty("spring.profiles.active", "simple");
        SpringApplication.run(GatewayApplication.class, args);
    }
}