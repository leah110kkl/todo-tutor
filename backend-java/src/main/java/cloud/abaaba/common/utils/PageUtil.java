package cloud.abaaba.common.utils;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * PageUtil
 *
 * @author Pig-Gua
 * @date 2025-05-27
 */
public class PageUtil {

    public static <T, R> IPage<R> convert(IPage<T> page, Function<T, R> function) {
        Page<R> convertPage = new Page<>();
        convertPage.setCurrent(page.getCurrent());
        convertPage.setSize(page.getSize());
        convertPage.setTotal(page.getTotal());
        convertPage.setRecords(page.getRecords().stream().map(function).collect(Collectors.toList()));
        return convertPage;
    }

}
