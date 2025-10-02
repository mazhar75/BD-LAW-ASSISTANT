package com.bdlaw.gateway.repository;

import com.bdlaw.gateway.entity.UserPreferences;
import com.bdlaw.gateway.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface UserPreferencesRepository extends JpaRepository<UserPreferences, Long> {

    Optional<UserPreferences> findByUser(User user);

    Optional<UserPreferences> findByUserId(Long userId);

    void deleteByUser(User user);
}