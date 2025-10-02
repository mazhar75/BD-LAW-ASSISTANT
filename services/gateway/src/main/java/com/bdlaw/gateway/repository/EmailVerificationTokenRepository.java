package com.bdlaw.gateway.repository;

import com.bdlaw.gateway.entity.EmailVerificationToken;
import com.bdlaw.gateway.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Optional;

@Repository
public interface EmailVerificationTokenRepository extends JpaRepository<EmailVerificationToken, Long> {

    Optional<EmailVerificationToken> findByToken(String token);

    Optional<EmailVerificationToken> findByUser(User user);

    @Query("SELECT t FROM EmailVerificationToken t WHERE t.user = :user AND t.verified = false AND t.expiryDate > :now")
    Optional<EmailVerificationToken> findValidTokenByUser(@Param("user") User user, @Param("now") LocalDateTime now);

    @Modifying
    @Transactional
    @Query("DELETE FROM EmailVerificationToken t WHERE t.expiryDate < :now")
    void deleteExpiredTokens(@Param("now") LocalDateTime now);

    @Modifying
    @Transactional
    @Query("UPDATE EmailVerificationToken t SET t.verified = true WHERE t.token = :token")
    void markAsVerified(@Param("token") String token);

    @Modifying
    @Transactional
    @Query("DELETE FROM EmailVerificationToken t WHERE t.user = :user")
    void deleteByUser(@Param("user") User user);
}