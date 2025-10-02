package com.bdlaw.gateway.service;

import com.bdlaw.gateway.entity.User;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class EmailService {

    @Value("${spring.application.name}")
    private String applicationName;

    @Value("${app.frontend.url:http://localhost:3000}")
    private String frontendUrl;

    public void sendVerificationEmail(User user, String verificationToken) {
        // TODO: Implement email sending logic
        // For now, just log the action
        log.info("Verification email would be sent to: {}", user.getEmail());

        // In production, you would integrate with an email service like:
        // - SendGrid
        // - AWS SES
        // - Spring Mail with SMTP

        String verificationLink = frontendUrl + "/verify-email?token=" + verificationToken;
        log.debug("Verification link: {}", verificationLink);
    }

    public void sendPasswordResetEmail(User user, String resetToken) {
        // TODO: Implement email sending logic
        log.info("Password reset email would be sent to: {}", user.getEmail());

        String resetLink = frontendUrl + "/reset-password?token=" + resetToken;
        log.debug("Password reset link: {}", resetLink);
    }

    public void sendWelcomeEmail(User user) {
        // TODO: Implement email sending logic
        log.info("Welcome email would be sent to: {}", user.getEmail());
    }

    public void sendAccountLockedEmail(User user) {
        // TODO: Implement email sending logic
        log.info("Account locked notification would be sent to: {}", user.getEmail());
    }

    public void sendPasswordChangedEmail(User user) {
        // TODO: Implement email sending logic
        log.info("Password changed notification would be sent to: {}", user.getEmail());
    }
}