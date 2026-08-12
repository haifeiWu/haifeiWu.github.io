---
categories: ["后端"]
title: "扒一扒spring，dom4j实现模拟实现读取xml"
date: "2017-08-23T20:38:56+08:00"
tags: ["Spring", "后端", "算法"]
summary: " 今天leadr提出需求，原来公司项目中读取解析xml文件的代码效率太低，考虑切换一种xml为数据封装格式与读取方式以提高效率。我这灵机一动spring对bean的依赖注入就是读取xml文件，可以尝试扒一扒spring的源码，来实现一个轻量级的方案。 重构xml文件，向sprin…"
translationKey: "bayibaspring-dom4jshixianmonishixianduquxml"
---

> 📌 本文原发布于掘金社区：[扒一扒spring，dom4j实现模拟实现读取xml](https://juejin.cn/post/6844903492453138446)

> 今天leadr提出需求，原来公司项目中读取解析xml文件的代码效率太低，考虑切换一种xml为数据封装格式与读取方式以提高效率。我这灵机一动spring对bean的依赖注入就是读取xml文件，可以尝试扒一扒spring的源码，来实现一个轻量级的方案。

## 重构xml文件，向spring的xml文件格式看齐

重构完成的xml文件格式如下：

``` ini
<?xml version="1.0" encoding="UTF-8"?>

<beans>
    <bean name="iaminformation" class="com.whf.readxml.model.IamConfig">
        <property name="iamUrl" value="http:192.168.7.154:8080" />
        <property name="token" value="abcdefg" />
        <property name="iamName" value="中电科" />
        <property name="sourceNumber" value="4" />
        <property name="timeSpan" value="12" />
    </bean>

    <bean name="plugin" class="com.whf.readxml.model.PluginAttributes">
        <property name="name" value="ADTest1" />
        <property name="pluginType" value="AdPlugin" />
        <property name="code" value="100001" />
        <property name="url" value="ldap://192.168.7.241:389" />
        <property name="adminPsw" value="1qaz2wsx2017" />
        <property name="adminName" value="QUARKDATA\administrator" />
        <property name="adDn" value="OU=test,DC=quarkdata,DC=com" />
        <property name="securityAuthentication" value="simple" />

        <property name="staffFieldMatch">
            <bean name="staffFieldMatch" class="com.whf.readxml.model.StaffFieldMatch">
                <property name="idField" value="objectGUID" />
                <property name="userNameField" value="sAMAccountName" />
                <property name="firstNameField" value="givenName" />
                <property name="lastNameField" value="sn" />
                <property name="displayNameField" value="displayName" />
                <property name="phoneNumberField" value="" />
                <property name="telField" value="homePhone" />
                <property name="emailField" value="email" />
            </bean>
        </property>

        <property name="orgFieldMatch">
            <bean name="orgFieldMatch" class="com.whf.readxml.model.OrgFieldMatch">
                <property name="idField" value="objectGUID" />
                <property name="nameField" value="name" />
                <property name="displayNameField" value="ou" />
            </bean>
        </property>

        <property name="groupFieldMatch">
            <bean name="groupFieldMatch" class="com.whf.readxml.model.GroupFieldMatch">
                <property name="idFied" value="objectGUID" />
                <property name="nameField" value="sAMAccountName" />
                <property name="displayNameField" value="displayName" />
                <property name="decriptionField" value="info" />
            </bean>
        </property>
    </bean>

    <bean name="plugin" class="com.whf.readxml.model.PluginAttributes">
        <property name="name" value="LDAPTest1" />
        <property name="pluginType" value="LdapPlugin" />
        <property name="code" value="100002" />
        <property name="url" value="ldap://192.168.7.245/" />
        <property name="adminPsw" value="test123456" />
        <property name="adminName" value="cn=admin,dc=thundersoft,dc=com" />
        <property name="adDn" value="dc=thundersoft,dc=com" />
        <property name="securityAuthentication" value="simple" />
        <property name="staffFieldMatch">
            <bean name="staffFieldMatch" class="com.whf.readxml.model.StaffFieldMatch">
                <property name="idField" value="gidNumber" />
                <property name="userNameField" value="uid" />
                <property name="firstNameField" value="givenName" />
                <property name="lastNameField" value="sn" />
                <property name="displayNameField" value="displayName" />
                <property name="phoneNumberField" value="telephoneNumber" />
                <property name="telField" value="tel" />
                <property name="emailField" value="email" />
            </bean>
        </property>

        <property name="orgFieldMatch">
            <bean name="orgFieldMatch" class="com.whf.readxml.model.OrgFieldMatch">
                <property name="idField" value="dn" />
                <property name="nameField" value="ou" />
                <property name="displayNameField" value="orgDisplayName" />
            </bean>
        </property>

        <property name="groupFieldMatch">
            <bean name="groupFieldMatch" class="com.whf.readxml.model.GroupFieldMatch">
                <property name="idFied" value="dn" />
                <property name="nameField" value="cn" />
                <property name="displayNameField" value="groupDisplayName" />
                <property name="decriptionField" value="description" />
            </bean>
        </property>
    </bean>
</beans>
```

看起来很眼熟的有没有，跟spring的配置文件一样哦。

## 扒一扒spring读取xml文件的源码

手动扒了一下spring读取xml文件的代码，由于spring过于庞大，读取spring的xml方法又按照读取不同的标签被分拆出n多个方法，楼主能力有限就不在这里卖弄了，不过spring从配置文件把bean加载到bean工厂跟楼主下面读取xml文件的方式理论上是一样的。

废话不多说，上代码：

``` ini
/**
 * 模拟spring依赖注入的方式读取xml文件.
 * @author whf
 * @date Aug 23, 2017
 */
public class XMLBeanFactory {

    private String xmlName;
    private SAXReader reader;
    private Document document;

    /**
     * 构造方法.
     * @param xmlName xmlName.
     */
    public XMLBeanFactory(String xmlName) { // 在构造方法中
        try {
            this.xmlName = xmlName;
            reader = new SAXReader();
            document = reader.read(this.getClass().getClassLoader().getResourceAsStream(xmlName));
        } catch (DocumentException e) {
            e.printStackTrace();
        }
    }

    /**
     * 获取相同类型的bean.
     * @param type bean的class type.
     * @return 返回相同类型的bean的list.
     * @throws Exception Exception.
     */
    public <T> List<T> getBeansOfType(Class<T> type) throws Exception {
        List<T> objects = new ArrayList<>();
        try {
            Element root = document.getRootElement();
            List<Element> beans = root.elements();
            if (beans.size() > 0) {
                for (Element bean : beans) {
                    if (bean.attributeValue("class").equals(type.getName())) {
                        T object = null;
                        String clazz = bean.attributeValue("class");
                        // 通过反射来创建对象
                        Class beanClass = Class.forName(clazz);
                        object = (T) beanClass.newInstance();

                        List<Element> propertys = bean.elements();

                        if (propertys.size() > 0) {
                            for (Element property : propertys) {
                                String key = property.attributeValue("name");
                                Field field = beanClass.getDeclaredField(key);
                                field.setAccessible(true);

                                List<Element> childBean = property.elements();

                                // 如果property下内嵌bean
                                if (childBean.size() > 0) {
                                    Object childObject = getBean(key, property);
                                    field.set(object, childObject);
                                } else {
                                    /*
                                     * 此属性值是一个字符串.这里单独处理int,float类型变量.如果不处理,
                                     * 会将String类型直接赋值给int类型,发生ClassCastException
                                     */
                                    String value = property.attributeValue("value");
                                    // 需要对类型进行判断
                                    if (field.getType().getName().equals("int")) {
                                        // 整数
                                        int x = Integer.parseInt(value);
                                        field.set(object, x);
                                        continue;
                                    }
                                    if (field.getType().getName().equals("float")) {
                                        // 浮点数
                                        float y = Float.parseFloat(value);
                                        field.set(object, y); // 注意double可以接受float类型
                                        continue;
                                    }
                                    field.set(object, value);// 处理String类型
                                }
                            }
                        }
                        objects.add(object);
                    }
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return objects;
    }
    /**
     * 获取property内嵌的bean.
     * @param name id或者bean的name
     * @param root 根节点.
     * @return 返回封装完整的bean.
     * @throws Exception Exception.
     */
    public Object getBean(String name, Element root) throws Exception {

        Object object = null;
        List<Element> beans = root.elements();
        if (beans.size() > 0) {
            for (Element bean : beans) {
                if (bean.attributeValue("name").equals(name)) {
                    // 如果bean name相同则开始创建对象
                    String clazz = bean.attributeValue("class");
                    // 通过反射来创建对象
                    Class beanClass = Class.forName(clazz);
                    object = beanClass.newInstance();

                    List<Element> propertys = bean.elements();

                    if (propertys.size() > 0) {
                        for (Element property : propertys) {
                            String key = property.attributeValue("name");
                            Field field = beanClass.getDeclaredField(key);
                            field.setAccessible(true);

                            List<Element> childBean = property.elements();

                            // 如果property下内嵌bean
                            if (childBean.size() > 0) {
                                field.set(object, getBean(key, property));
                            }

                            if (property.attribute("ref") != null) {
                                /*
                                 * 此属性的值是一个对象.这里由于直接调用getBean方法赋值给对象,返回的对象一定是Bean参数的对象, 因此强制转换不会出问题
                                 */
                                String refid = property.attributeValue("ref");
                                field.set(object, getBean(refid));
                            } else {
                                /*
                                 * 此属性值是一个字符串.这里单独处理int,float类型变量.如果不处理,会将String类型直接赋值给int类型,
                                 * 发生ClassCastException
                                 */
                                String value = property.attributeValue("value");
                                // 需要对类型进行判断
                                field.set(object, value);// 处理String类型
                            }
                        }
                    }

                }
            }
        }

        return object;
    }

}
```

楼主的代码就是实现读取xml文件中相同类型的bean封装到list中返回。具体如何实现，看代码，注释写的很清楚了。

## 文件读取的效率提升120多倍

代码完成之后，对比之前的读取xml的代码，比之前的效率提升了120。

## 总结一下

大牛都说要看开源框架的源码，收获会怎样怎样，但是对于大部分向我这样的伪码农去扒源码的时候总是一头雾水，不知所云。然而，当我们真正有需求的时候，开源代码的实现便成了一份巨大的宝藏，带着我们的目的去扒源码，有时候会有事半功倍的效果。楼主亲测有效，源码虽好，可不要贪杯哦。
