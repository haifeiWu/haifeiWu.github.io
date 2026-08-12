---
categories: ["后端"]
title: "Spring aop 实现权限管理"
date: "2017-12-06T19:45:36+08:00"
tags: ["后端"]
summary: "最近项目中需要做一个权限管理模块，按照之前同事的做法是在 controller 层的每个接口调用之前上做逻辑判断，这样做也没有不妥，但是代码重复率太高，而且是体力劳动，so，便有了如题所说的使用 Spring aop 做一个切点来实现通用功能的权限管理，这样也就降低了项目后期开发的可扩…"
translationKey: "spring-aopshixianquanxianguanli"
---

> 📌 本文原发布于掘金社区：[Spring aop 实现权限管理](https://juejin.cn/post/6844903519649005575)

# 问题源于项目开发

最近项目中需要做一个权限管理模块，按照之前同事的做法是在 controller 层的每个接口调用之前做逻辑判断，这样做也没有不妥，但是代码重复率太高，而且是体力劳动，so，便有了如题所说的使用 Spring aop 做一个切点来实现通用功能的权限管理，这样也就降低了项目后期开发的可扩展性。

# 权限管理的代码实现与配置文件

在最小的代码修改程度上，aop 无疑是最理想的选择。项目中有各种权限复合的情况，相对来说逻辑复杂度比较高，所以一步步来。因为权限涉及到的是后端接口的调用，所以楼主选择在 controller 层代码上做切面，而切点就是 controller 中的各个方法块，对于通用访问权限，我们使用 execution 表达式进行排除。

## 只读管理员权限的实现及切点选择

对于实现排除通用的 controller，楼主采用的是 execution 表达式逻辑运算。因为只读管理员拥有全局读权限，而对于增删改权限，楼主采用切点切入增删改的方法，so，这个时候规范的方法命名就很重要了。对于各种与只读管理员复合的管理员，我们在代码中做一下特殊判断即可。下面是 Spring aop 的配置文件的配置方法。

``` bash

<!--非法权限抛出异常的spring mvc的处理-->
<bean class="org.springframework.web.servlet.handler.SimpleMappingExceptionResolver">
    <property name="exceptionMappings">
        <props>
            <prop key="com.thundersoft.metadata.exception.AccessDeniedException">forward:/auth/readOnly</prop>
        </props>
    </property>
</bean>
    
 <bean id="usersPermissionsAdvice"
          class="com.thundersoft.metadata.aop.UsersPermissionsAdvice"/>
    <aop:config>
        <!--定义切面 -->
            <!-- 定义切入点 (配置在com.thundersoft.metadata.web.controller下所有的类在调用之前都会被拦截) -->
                    expression="(execution(* com.thundersoft.metadata.web.controller.*.add*(..)) or
                    execution(* com.thundersoft.metadata.web.controller.*.edit*(..)) or
                    execution(* com.thundersoft.metadata.web.controller.*.del*(..)) or
                    execution(* com.thundersoft.metadata.web.controller.*.update*(..)) or
                    execution(* com.thundersoft.metadata.web.controller.*.insert*(..)) or
                    execution(* com.thundersoft.metadata.web.controller.*.modif*(..))) or
                    execution(* com.thundersoft.metadata.web.controller.*.down*(..))) and (
                    !execution(* com.thundersoft.metadata.web.controller.FindPasswordController.*(..)) and
                    !execution(* com.thundersoft.metadata.web.controller.SelfServiceController.*(..)) and
                    !execution(* com.thundersoft.metadata.web.controller.HomeController.*(..)) and
                    !execution(* com.thundersoft.metadata.web.controller.UserStatusController.*(..)) and
                    !execution(* com.thundersoft.metadata.web.controller.DashboardController.*(..)) and
                    !execution(* com.thundersoft.metadata.web.controller.MainController.*(..))))"
                    id="authPointCut"/>
            <!--方法被调用之前执行的 -->
                        pointcut-ref="authPointCut"/>
        </aop:aspect>
```

## 只读管理员权限管理代码实现

上面说了那么多，废话不多说了，下面是对只读权限与各种复合权限进行控制的切面代码实现。

``` bash
 /**
     * 对只读管理员以及其复合管理员进行aop拦截判断.
     * @param joinPoint 切入点.
     * @throws IOException
     */
    public void readOnly(JoinPoint joinPoint) throws IOException {

        /**
         * 获取被拦截的方法.
         */
        String methodName = joinPoint.getSignature().getName();

        /**
         * 获取被拦截的对象.
         */
        Object object = joinPoint.getTarget();

        logger.info("权限管理aop,方法名称{}" + methodName);
        HttpServletRequest request =((ServletRequestAttributes) RequestContextHolder.getRequestAttributes()).getRequest();
        HttpServletResponse response =((ServletRequestAttributes) RequestContextHolder.getRequestAttributes()).getResponse();
        String roleFlag = GetLoginUserInfor.getLoginUserRole(request);

        /**
         * 超级管理员
         */
        if (PermissionsLabeled.super_Admin.equals(roleFlag)) {
            return;
        }

        /**
         * 只读管理员做数据更改权限的判断
         */
        if (PermissionsLabeled.reader_Admin.equals(roleFlag)) {
            if (methodName.contains("redirectToLogout")) {
                return;
            }
            logger.error("只读管理员无操作权限!");
            throw new AccessDeniedException("您无权操作！");
        }

        /**
         * 部门管理员,且为只读管理员,
         */
        if (PermissionsLabeled.dept_reader_Admin.equals(roleFlag)) {
            if (object instanceof DepartmentController) {
                return;
            }

            if (object instanceof UserController) {
                if (methodName.contains("addAdmin")) {
                    throw new AccessDeniedException("您无权操作！");
                }

                if (methodName.contains("deleteAdmin")) {
                    throw new AccessDeniedException("您无权操作！");
                }

                if (methodName.contains("updateAdmin")) {
                    throw new AccessDeniedException("您无权操作！");
                }
                return;
            }

            if (object instanceof GroupController) {
                return;
            }
            logger.error("部门管理员,且为只读管理员无操作权限!");
            throw new AccessDeniedException("您无权操作！");
        }

        /**
         * 应用管理员,且为只读管理员
         */
        if (PermissionsLabeled.app_reader_Admin.equals(roleFlag)) {
            if (object instanceof AppController) {
                return;
            }

            if (object instanceof AppPolicyController) {
                return;
            }
            logger.error("应用管理员,且为只读管理员无操作权限!");
            throw new AccessDeniedException("您无权操作！");
        }

        /**
         * 部门管理员,且为应用管理员,且为只读管理员
         */
        if (PermissionsLabeled.dept_app_reader_Admin.equals(roleFlag)) {
            if (object instanceof DepartmentController) {
                return;
            }

            if (object instanceof UserController) {
                return;
            }

            if (object instanceof GroupController) {
                return;
            }

            if (object instanceof AppController) {
                return;
            }

            if (object instanceof AppPolicyController) {
                return;
            }
            logger.error("部门管理员,且为应用管理员,且为只读管理员无操作权限");
            throw new AccessDeniedException("您无权操作！");
        }
    }
```

## 具有专门功能的管理员权限控制的切点选择

因为具有专门的管理员权限比较特殊，楼主采用的方式是除了通用访问权限之外的 controller 全切，特殊情况在代码逻辑里面实现即可。配置文件代码如下：

``` bash
        <!--定义切面 -->
            <!-- 定义切入点 (配置在com.thundersoft.metadata.web.controller下所有的类在调用之前都会被拦截) -->
                    expression="(execution(* com.thundersoft.metadata.web.controller.*.*(..)) and (
                    !execution(* com.thundersoft.metadata.web.controller.FindPasswordController.*(..)) and
                    !execution(* com.thundersoft.metadata.web.controller.SelfServiceController.*(..)) and
                    !execution(* com.thundersoft.metadata.web.controller.HomeController.*(..)) and
                    !execution(* com.thundersoft.metadata.web.controller.UserStatusController.*(..)) and
                    !execution(* com.thundersoft.metadata.web.controller.DashboardController.*(..)) and
                    !execution(* com.thundersoft.metadata.web.controller.MainController.*(..))))"
                    id="appAuthPointCut"/>
            <!--方法被调用之前执行的 -->
                        pointcut-ref="appAuthPointCut"/>
```

## 权限管理的切面代码实现

``` bash
 /**
     * 对应用管理员以及部门管理员进行aop拦截判断.
     * @param joinPoint 切入点.
     * @throws IOException
     */
    public void appDeptAuth(JoinPoint joinPoint) throws IOException {
        /**
         * 获取被拦截的方法.
         */
        String methodName = joinPoint.getSignature().getName();

        /**
         * 获取被拦截的对象.
         */
        Object object = joinPoint.getTarget();

        logger.info("权限管理aop,方法名称{}",methodName);
        HttpServletRequest request =((ServletRequestAttributes) RequestContextHolder.getRequestAttributes()).getRequest();
        HttpServletResponse response =((ServletRequestAttributes) RequestContextHolder.getRequestAttributes()).getResponse();
        String roleFlag = GetLoginUserInfor.getLoginUserRole(request);

        /**
         * 超级管理员
         */
        if (PermissionsLabeled.super_Admin.equals(roleFlag)) {
            return;
        }

        /**
         * 应用管理员做数据更改权限的判断
         */
        if (PermissionsLabeled.app_Admin.equals(roleFlag)) {
            if (object instanceof AppController) {
                return;
            }

            if (object instanceof AppPolicyController) {
                return;
            }

            logger.error("应用管理员无操作权限");
            throw new AccessDeniedException("您无权操作！");
        } else if (PermissionsLabeled.dept_Admin.equals(roleFlag)) {
            if (object instanceof DepartmentController) {
                return;
            }

            if (object instanceof UserController) {
                return;
            }

            if (object instanceof GroupController) {
                return;
            }
            if ("getAllDepartments".equals(methodName)) {
                return;
            }
            logger.error("应用管理员无操作权限");
            throw new AccessDeniedException("您无权操作！");
        } else {
            return;
        }
    }
```

## 自定义权限非法异常代码

``` bash

/**
 * @author wuhf0703@thundersoft.com
 * @date 2017/12/12
 */
public class AccessDeniedException extends RuntimeException {

    /**
     * Constructs a <code>AccessDeniedException</code> with the specified message.
     *
     * @param msg the detail message.
     */
    public AccessDeniedException(String msg) {
        super(msg);
    }

    /**
     * Constructs a {@code AccessDeniedException} with the specified message and root cause.
     *
     * @param msg the detail message.
     * @param t root cause
     */
    public AccessDeniedException(String msg, Throwable t) {
        super(msg, t);
    }
}
```

<a href="https://link.juejin.cn?target=http%3A%2F%2Fblog.csdn.net%2Fgithub_36379934%2Farticle%2Fdetails%2F78734075" target="_blank" data-ref="nofollow noopener noreferrer" title="http://blog.csdn.net/github_36379934/article/details/78734075">博客首发链接</a>
