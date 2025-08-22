package cloud.abaaba.common.utils;

import java.util.List;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * ListUtil
 *
 * @author Pig-Gua
 * @date 2025-06-16
 */
public class ListUtil {

    public static <T, R> List<R> convert(List<T> page, Function<T, R> function) {
        return page.stream().map(function).collect(Collectors.toList());
    }

}
