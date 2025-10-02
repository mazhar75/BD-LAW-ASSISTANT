package com.bdlaw.gateway.repository;

import com.bdlaw.gateway.entity.Role;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface RoleRepository extends JpaRepository<Role, Long> {

    Optional<Role> findByName(String name);

    boolean existsByName(String name);

    @Query(value = "SELECT r.* FROM auth.roles r " +
                   "JOIN auth.user_roles ur ON r.id = ur.role_id " +
                   "WHERE ur.user_id = :userId", nativeQuery = true)
    List<Role> findRolesByUserId(@Param("userId") Long userId);
}