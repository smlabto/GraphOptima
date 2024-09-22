global weight_checkbox_values color_by_iterations

% Load the data
data = load('Ukraine_Feb_22_scalarization_cuGraph_500_budget_6_generator_1_evaluator_paramRange_100000.mat');

% Calculate iteration ratio
unique_weights = unique(data.weights, 'rows');
n_weights = size(unique_weights, 1);
data.iteration_ratio = zeros(size(data.iteration_number));
weight_checkbox_values = zeros(n_weights, 1);

for i = 1:n_weights
    weight = unique_weights(i, :);
    idx = all(data.weights == weight, 2);
    total_iter = max(data.iteration_number(idx));
    data.iteration_ratio(idx) = data.iteration_number(idx) / total_iter;
end

% Compute inverse of normalized edge length variance
data.normalized_edge_length_variance_inv = 1 - data.normalized_edge_length_variance;


% Create the scatter plot
figure;
hold on;

hAx = gca;

% Set grid style
hAx.GridLineStyle = '-';
hAx.MinorGridLineStyle = '-';
% Enable grid
hAx.XGrid = 'on';
hAx.YGrid = 'on';
hAx.ZGrid = 'on';
hAx.XMinorGrid = 'on';
hAx.YMinorGrid = 'on';
hAx.ZMinorGrid = 'on';

% Color by weight category
color_by_iterations = false;

% Assign colors to weight groups
colors = lines(n_weights); % Create a colormap with n_weights distinct colors

% Create a checkbox for each weight group
for i = 1:n_weights
    weight = unique_weights(i, :);
    weight_checkbox_values(i) = 1;
    uicontrol('Style', 'checkbox', ...
            'String', sprintf('Color weights: %.1f, %.1f, %.1f', weight(1), weight(2), weight(3)), ...
            'Value', weight_checkbox_values(i), ...
            'Position', [20 20+20*i 200 20], ...
            'Callback', {@weight_checkbox_callback, i, hAx, data, unique_weights, n_weights, colors});
end

% Initialize the plot
update_plot(hAx, data, unique_weights, n_weights, color_by_iterations, weight_checkbox_values, colors);

% Add a checkbox to switch between color modes
hCheckbox = uicontrol('Style', 'checkbox', ...
                      'String', 'Color by iteration ratio', ...
                      'Value', color_by_iterations, ...
                      'Position', [20 20 200 20], ...
                      'Callback', {@checkbox_callback, hAx, data, unique_weights, n_weights, colors});
fig2plotly(gcf, 'offline', false);
hold off;

% Set the title, labels, and legend
title('Crosslessness, Inverse of Normalized Edge Length Variance and Min Angle');
xlabel('Crosslessness');
ylabel('Inverse of Normalized Edge Length Variance');
zlabel('Min Angle');
legend('Location', 'best');

% Customize data cursor display
dcm_obj = datacursormode(gcf);
set(dcm_obj, 'UpdateFcn', {@myupdatefcn, data});

% Custom update function for data cursor
function output_txt = myupdatefcn(obj, event_obj, data)
    pos = get(event_obj, 'Position');
    
    % Find the index of the data point
    idx = find(data.crosslessness == pos(1) & data.normalized_edge_length_variance_inv == pos(2) & data.min_angle == pos(3), 1, 'first');
    
    % Display additional information
    output_txt = {...
        ['Crosslessness: ', num2str(pos(1))], ...
        ['Inverse of Normalized Edge Length Variance: ', num2str(pos(2))], ...
        ['Min Angle: ', num2str(pos(3))], ...
        ['Scaling Factor: ', num2str(data.scaling_factor(idx))], ...
        ['Gravity: ', num2str(data.gravity(idx))], ...
        ['Max Iter: ', num2str(data.max_iter(idx))] ...
        };
end

function checkbox_callback(src, ~, hAx, data, unique_weights, n_weights, colors)
    global weight_checkbox_values color_by_iterations
    color_by_iterations = get(src, 'Value');
    update_plot(hAx, data, unique_weights, n_weights, color_by_iterations, weight_checkbox_values, colors);
end

function weight_checkbox_callback(src, ~, index, hAx, data, unique_weights, n_weights, colors)
    global weight_checkbox_values color_by_iterations
    weight_checkbox_values(index) = get(src, 'Value');
    update_plot(hAx, data, unique_weights, n_weights, color_by_iterations, weight_checkbox_values, colors);
end

function update_plot(hAx, data, unique_weights, n_weights, color_by_iterations, weight_checkbox_values, colors)
    cla(hAx);
    hold on;

    if color_by_iterations
        % First, draw all points in gray
        scatter3(data.crosslessness, data.normalized_edge_length_variance_inv, data.min_angle, 'MarkerFaceColor', [0.5, 0.5, 0.5], 'MarkerEdgeColor', [0.5, 0.5, 0.5]);

        for i = 1:n_weights
            weight = unique_weights(i, :);
            idx = all(data.weights == weight, 2);
            if weight_checkbox_values(i)
                % Overplot colored points
                scatter3(data.crosslessness(idx), data.normalized_edge_length_variance_inv(idx), data.min_angle(idx), [], data.iteration_ratio(idx), 'filled');
            end
        end
        colormap(jet); % Choose a colormap
        hColorbar = colorbar;
        ylabel(hColorbar, 'Iteration ratio');
        legend(hAx, 'off'); % Hide legend for weight category
    else
        % Color by weight category
        % First, draw all points in gray
        scatter3(data.crosslessness, data.normalized_edge_length_variance_inv, data.min_angle, 'MarkerFaceColor', [0.5, 0.5, 0.5], 'MarkerEdgeColor', [0.5, 0.5, 0.5]);
        % Remove the legend entry for the gray points
        h = findobj(gca, 'Type', 'scatter');
        set(get(get(h(1),'Annotation'),'LegendInformation'),'IconDisplayStyle','off');

        for i = 1:n_weights
            weight = unique_weights(i, :);
            idx = all(data.weights == weight, 2);
            if weight_checkbox_values(i)
                clr = colors(i, :); % Use the assigned color for the weight group
                scatter3(data.crosslessness(idx), data.normalized_edge_length_variance_inv(idx), data.min_angle(idx), ...
                'DisplayName', sprintf('Weights: %.1f, %.1f, %.1f', weight(1), weight(2), weight(3)), ...
                'MarkerFaceColor', clr, 'MarkerEdgeColor', clr);
            end
        end
        colorbar(hAx, 'off'); % Hide colorbar for iteration ratio
        legend(hAx, 'Location', 'best');
    end

    % Add a red dot at the point (1,1,1) and label it
    % scatter3(1, 1, 1, 'red', 'filled');
    % text(1, 1, 1, 'Utopia Point', 'Color', 'red');

    hold off;
end

