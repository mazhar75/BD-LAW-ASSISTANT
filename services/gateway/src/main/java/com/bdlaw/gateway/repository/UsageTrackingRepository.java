package com.bdlaw.gateway.repository;

import com.bdlaw.gateway.entity.UsageTracking;
import com.bdlaw.gateway.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Repository
public interface UsageTrackingRepository extends JpaRepository<UsageTracking, Long> {

    Page<UsageTracking> findByUser(User user, Pageable pageable);

    Page<UsageTracking> findByUserAndDateBetween(User user, LocalDateTime startDate, LocalDateTime endDate, Pageable pageable);

    @Query("SELECT COUNT(u) FROM UsageTracking u WHERE u.user = :user AND u.date >= :startDate")
    Long countByUserSince(@Param("user") User user, @Param("startDate") LocalDateTime startDate);

    @Query("SELECT u.endpoint, COUNT(u) as count FROM UsageTracking u WHERE u.user = :user GROUP BY u.endpoint ORDER BY count DESC")
    List<Object[]> findTopEndpointsByUser(@Param("user") User user);

    @Query("SELECT AVG(u.responseTimeMs) FROM UsageTracking u WHERE u.user = :user AND u.date >= :startDate")
    Double getAverageResponseTimeByUserSince(@Param("user") User user, @Param("startDate") LocalDateTime startDate);

    @Query("SELECT DATE(u.date) as day, COUNT(u) as count FROM UsageTracking u WHERE u.user = :user AND u.date >= :startDate GROUP BY DATE(u.date) ORDER BY day")
    List<Object[]> getDailyUsageByUserSince(@Param("user") User user, @Param("startDate") LocalDateTime startDate);

    @Query("SELECT COUNT(DISTINCT u.user) FROM UsageTracking u WHERE u.date >= :startDate")
    Long countActiveUsersSince(@Param("startDate") LocalDateTime startDate);

    void deleteByDateBefore(LocalDateTime date);
}