package com.bdlaw.gateway.interceptor;

import com.bdlaw.gateway.entity.User;
import com.bdlaw.gateway.service.UserService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.ModelAndView;

@Component
@RequiredArgsConstructor
@Slf4j
public class UsageTrackingInterceptor implements HandlerInterceptor {

    private final UserService userService;
    private static final ThreadLocal<Long> requestStartTime = new ThreadLocal<>();

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        requestStartTime.set(System.currentTimeMillis());
        return true;
    }

    @Override
    public void postHandle(HttpServletRequest request, HttpServletResponse response, Object handler,
                          ModelAndView modelAndView) {
        // Method can be used for additional processing if needed
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        try {
            Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
            if (authentication != null && authentication.isAuthenticated() &&
                !authentication.getPrincipal().equals("anonymousUser")) {

                String username = authentication.getName();
                User user = userService.loadUserByUsername(username);

                Long startTime = requestStartTime.get();
                Long responseTime = startTime != null ? System.currentTimeMillis() - startTime : null;

                String endpoint = request.getRequestURI();
                String method = request.getMethod();
                int statusCode = response.getStatus();
                String userAgent = request.getHeader("User-Agent");
                String ipAddress = getClientIpAddress(request);
                String query = request.getQueryString();

                // Track usage asynchronously to avoid impacting response time
                userService.trackUsage(user, endpoint, method, statusCode, responseTime,
                                     query, userAgent, ipAddress);
            }
        } catch (Exception e) {
            log.error("Failed to track usage", e);
        } finally {
            requestStartTime.remove();
        }
    }

    private String getClientIpAddress(HttpServletRequest request) {
        String xForwardedFor = request.getHeader("X-Forwarded-For");
        if (xForwardedFor != null && !xForwardedFor.isEmpty()) {
            return xForwardedFor.split(",")[0].trim();
        }

        String xRealIp = request.getHeader("X-Real-IP");
        if (xRealIp != null && !xRealIp.isEmpty()) {
            return xRealIp;
        }

        return request.getRemoteAddr();
    }
}