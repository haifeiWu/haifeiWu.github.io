---
categories: ["后端"]
title: "lang3 的 split 方法误用"
date: "2019-08-07T13:53:17+08:00"
tags: ["Java"]
summary: "apache 的 lang3 是我们开发常用到的三方工具包，然而对这个包不甚了解的话，会产生莫名其秒的 bug ，在这里做下记录。 通过分析字符串的拆分结果，发现该方法并不是将分隔符去截取字符串，而是将分隔符的每一个字符都当成分隔符去截取字符串，当我们的分隔符是一个字符的时候一…"
translationKey: "lang3-de-split-fangfawuyong"
---

> 📌 本文原发布于掘金社区：[lang3 的 split 方法误用](https://juejin.cn/post/6844903907877978125)

<a href="https://link.juejin.cn?target=https%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2019%2Fade9%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="https://www.hchstudio.cn/article/2019/ade9/">lang3 的 split 方法误用-原文链接</a>\
apache 的 lang3 是我们开发常用到的三方工具包，然而对这个包不甚了解的话，会产生莫名其秒的 bug ，在这里做下记录。

## 误用示例

``` java
public class TestDemo {

    @Test
    public void test() throws IOException {
        String sendMsg = "{"expiredTime":"20190726135831","drives":"androidgetui","msgBody":"{\\"serialNumber\\":\\"wow22019072611349502\\",\\"push_key\\":\\"appactive#549110277\\",\\"title\\":\\"\\xe6\\x9c\\x89\\xe4\\xba\\xba@\\xe4\\xbd\\xa0\\",\\"message\\":\\"\\xe4\\xbb\\x8a\\xe5\\xa4\\xa9\\xe5\\x87\\xa0\\xe7\\x82\\xb9\\xe5\\x87\\xba\\xe5\\x8f\\x91\\xef\\xbc\\x9f\\",\\"link\\":\\"chelaile://homeTab/home?select=3\\",\\"open_type\\":0,\\"expireDays\\":\\"30\\",\\"type\\":14}","clients":["13065ffa4e25c4a7c68"]}CHELAILE_PUSH{"cityId":"007","gpsTime":"2019-07-24 21:33:06","lat":"30.605916","lng":"103.980439","s":"android","sourceUdid":"a4419b93-fb0e-43c7-98fa-5b7c18255660","token":"13065ffa4e25c4a7c68","tokenType":"3","udid":"UDID2TOKEN#a4419b93-fb0e-43c7-98fa-5b7c18255660","userCreateTime":"2018-04-20 08:13:32","userLastActiveTime":"2019-07-24 21:33:06","vc":"150"}";
        String[] dataArr = StringUtils.split(sendMsg,"CHELAILE_PUSH");
        Assert.assertEquals(dataArr.length,2);
    }
}
```

## 分析原因

通过分析字符串的拆分结果，发现该方法并不是将分隔符去截取字符串，而是将分隔符的每一个字符都当成分隔符去截取字符串，当我们的分隔符是一个字符的时候一般不会出现上面示例中出现的问题，如果分隔符是多个字符的时候这个问题就显现出来了。

## 查看 StringUtils 源码

``` java
    /**
     * 
     * <pre>
     * StringUtils.split(null, *)         = null
     * StringUtils.split("", *)           = []
     * StringUtils.split("abc def", null) = ["abc", "def"]
     * StringUtils.split("abc def", " ")  = ["abc", "def"]
     * StringUtils.split("abc  def", " ") = ["abc", "def"]
     * StringUtils.split("ab:cd:ef", ":") = ["ab", "cd", "ef"]
     * </pre>
     *
     * @param str  要解析的字符串，可能为空
     * @param separatorChars  用做分割字符的字符们（注意是字符串们哦！），当 separatorChars 传入的值为空的时候则用空格来做分隔符
     */
    public static String[] split(final String str, final String separatorChars) {
        return splitWorker(str, separatorChars, -1, false);
    }
    
    /**
     * Performs the logic for the {@code split} and
     * {@code splitPreserveAllTokens} methods that return a maximum array
     * length.
     *
     * @param str  the String to parse, may be {@code null}
     * @param separatorChars the separate character
     * @param max  the maximum number of elements to include in the
     *  array. A zero or negative value implies no limit.
     * @param preserveAllTokens if {@code true}, adjacent separators are
     * treated as empty token separators; if {@code false}, adjacent
     * separators are treated as one separator.
     * @return an array of parsed Strings, {@code null} if null String input
     */
    private static String[] splitWorker(final String str, final String separatorChars, final int max, final boolean preserveAllTokens) {
        // Performance tuned for 2.0 (JDK1.4)
        // Direct code is quicker than StringTokenizer.
        // Also, StringTokenizer uses isSpace() not isWhitespace()

        if (str == null) {
            return null;
        }
        final int len = str.length();
        if (len == 0) {
            return ArrayUtils.EMPTY_STRING_ARRAY;
        }
        final List<String> list = new ArrayList<>();
        int sizePlus1 = 1;
        int i = 0, start = 0;
        boolean match = false;
        boolean lastMatch = false;
        if (separatorChars == null) {
            
            // 用空格作为分隔符切割字符串
            while (i < len) {
                if (Character.isWhitespace(str.charAt(i))) {
                    if (match || preserveAllTokens) {
                        lastMatch = true;
                        if (sizePlus1++ == max) {
                            i = len;
                            lastMatch = false;
                        }
                        list.add(str.substring(start, i));
                        match = false;
                    }
                    start = ++i;
                    continue;
                }
                lastMatch = false;
                match = true;
                i++;
            }
        } else if (separatorChars.length() == 1) {
            // 分隔符的字符数为 1 的时候，切割字符串的逻辑
            final char sep = separatorChars.charAt(0);
            while (i < len) {
                if (str.charAt(i) == sep) {
                    if (match || preserveAllTokens) {
                        lastMatch = true;
                        if (sizePlus1++ == max) {
                            i = len;
                            lastMatch = false;
                        }
                        list.add(str.substring(start, i));
                        match = false;
                    }
                    start = ++i;
                    continue;
                }
                lastMatch = false;
                match = true;
                i++;
            }
        } else {
            // 当分隔符的字符数为多个的时候，分割字符串的逻辑
            // 示例：分隔字符串 abc，分割字符串的分隔符可以是 a,ab,abc
            while (i < len) {
                if (separatorChars.indexOf(str.charAt(i)) >= 0) {
                    if (match || preserveAllTokens) {
                        lastMatch = true;
                        if (sizePlus1++ == max) {
                            i = len;
                            lastMatch = false;
                        }
                        list.add(str.substring(start, i));
                        match = false;
                    }
                    start = ++i;
                    continue;
                }
                lastMatch = false;
                match = true;
                i++;
            }
        }
        if (match || preserveAllTokens && lastMatch) {
            list.add(str.substring(start, i));
        }
        return list.toArray(new String[list.size()]);
    }
```

## 小结

平时只知道调用api，在使用三方包的时候，没有认真查看api文档，对于三方包的方法，使用处于想当然的状态，这里应该做好反省。
