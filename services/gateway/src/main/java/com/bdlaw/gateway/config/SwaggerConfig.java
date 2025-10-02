package com.bdlaw.gateway.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.Arrays;
import java.util.List;

@Configuration
public class SwaggerConfig {

    @Value("${app.version:1.0.0}")
    private String appVersion;

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(getApiInfo())
            .servers(getServers())
            .components(getComponents())
            .addSecurityItem(new SecurityRequirement().addList("JWT Bearer Token"))
            .addSecurityItem(new SecurityRequirement().addList("API Key"));
    }

    private Info getApiInfo() {
        return new Info()
            .title("BD Law Assistant API Gateway")
            .description("API Gateway for Bangladesh Law Assistant System - A comprehensive legal information retrieval system")
            .version(appVersion)
            .contact(new Contact()
                .name("BD Law Team")
                .email("support@bdlaw.com")
                .url("https://bdlaw.com"))
            .license(new License()
                .name("Apache 2.0")
                .url("http://www.apache.org/licenses/LICENSE-2.0.html"));
    }

    private List<Server> getServers() {
        return Arrays.asList(
            new Server()
                .url("http://localhost:8080")
                .description("Local Development Server"),
            new Server()
                .url("https://api.bdlaw.com")
                .description("Production Server")
        );
    }

    private Components getComponents() {
        return new Components()
            .addSecuritySchemes("JWT Bearer Token",
                new SecurityScheme()
                    .type(SecurityScheme.Type.HTTP)
                    .scheme("bearer")
                    .bearerFormat("JWT")
                    .description("JWT Bearer token for authentication. Get token from /api/auth/login endpoint"))
            .addSecuritySchemes("API Key",
                new SecurityScheme()
                    .type(SecurityScheme.Type.APIKEY)
                    .in(SecurityScheme.In.HEADER)
                    .name("X-API-Key")
                    .description("API Key for service-to-service authentication"));
    }
}